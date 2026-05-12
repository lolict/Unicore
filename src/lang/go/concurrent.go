// UniCore 并发加速层 - Go实现
// 高性能并发、网络通信、流式处理

package unicore

import (
	"context"
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

// Pipeline 并行处理管道
type Pipeline struct {
	stages   []Stage
	wg       sync.WaitGroup
	ctx      context.Context
	cancel   context.CancelFunc
}

// Stage 处理阶段
type Stage struct {
	Name    string
	Handler func(interface{}) interface{}
}

// NewPipeline 创建新管道
func NewPipeline(name string, stages ...Stage) *Pipeline {
	ctx, cancel := context.WithCancel(context.Background())
	return &Pipeline{
		stages: stages,
		ctx:    ctx,
		cancel: cancel,
	}
}

// Run 执行管道
func (p *Pipeline) Run(input <-chan interface{}) <-chan interface{} {
	output := make(chan interface{})

	p.wg.Add(len(p.stages))
	for i, stage := range p.stages {
		go func(s Stage, in <-chan interface{}) {
			defer p.wg.Done()
			for item := range in {
				select {
				case <-p.ctx.Done():
					return
				default:
					result := s.Handler(item)
					if i == len(p.stages)-1 {
						output <- result
					}
				}
			}
		}(stage, input)
	}

	go func() {
		p.wg.Wait()
		close(output)
	}()

	return output
}

// Stop 停止管道
func (p *Pipeline) Stop() {
	p.cancel()
}

// WorkerPool 并行工作池
type WorkerPool struct {
	workers    int
	taskQueue  chan Task
	resultChan chan Result
	wg         sync.WaitGroup
	ctx        context.Context
	cancel     context.CancelFunc
}

// Task 任务定义
type Task struct {
	ID      uint64
	Payload interface{}
}

// Result 结果定义
type Result struct {
	TaskID uint64
	Data   interface{}
	Error  error
}

// NewWorkerPool 创建工作池
func NewWorkerPool(workers int) *WorkerPool {
	ctx, cancel := context.WithCancel(context.Background())
	return &WorkerPool{
		workers:    workers,
		taskQueue:  make(chan Task, workers*10),
		resultChan: make(chan Result, workers*10),
		ctx:        ctx,
		cancel:     cancel,
	}
}

// Start 启动工作池
func (wp *WorkerPool) Start(handler func(Task) Result) {
	for i := 0; i < wp.workers; i++ {
		wp.wg.Add(1)
		go func() {
			defer wp.wg.Done()
			for task := range wp.taskQueue {
				select {
				case <-wp.ctx.Done():
					return
				default:
					result := handler(task)
					wp.resultChan <- result
				}
			}
		}()
	}
}

// Submit 提交任务
func (wp *WorkerPool) Submit(task Task) {
	select {
	case wp.taskQueue <- task:
	case <-wp.ctx.Done():
	}
}

// Results 获取结果通道
func (wp *WorkerPool) Results() <-chan Result {
	return wp.resultChan
}

// Stop 停止工作池
func (wp *WorkerPool) Stop() {
	wp.cancel()
	close(wp.taskQueue)
	wp.wg.Wait()
	close(wp.resultChan)
}

// ParallelExecutor 并行执行器
type ParallelExecutor struct {
	maxGoroutines int
	semaphore     chan struct{}
	wg            sync.WaitGroup
}

// NewParallelExecutor 创建并行执行器
func NewParallelExecutor(maxGoroutines int) *ParallelExecutor {
	return &ParallelExecutor{
		maxGoroutines: maxGoroutines,
		semaphore:      make(chan struct{}, maxGoroutines),
	}
}

// Parallel 并行执行函数
func (pe *ParallelExecutor) Parallel(tasks ...func()) {
	for _, task := range tasks {
		pe.semaphore <- struct{}{}
		pe.wg.Add(1)
		go func(t func()) {
			defer pe.wg.Done()
			defer func() { <-pe.semaphore }()
			t()
		}(task)
	}
}

// Wait 等待完成
func (pe *ParallelExecutor) Wait() {
	pe.wg.Wait()
}

// MapReduce 分布式计算
func MapReduce(mapFunc func(interface{}) []interface{}, reduceFunc func([]interface{}) interface{}, data []interface{}) interface{} {
	
	mapResults := make(chan []interface{}, len(data))
	
	var wg sync.WaitGroup
	for _, item := range data {
		wg.Add(1)
		go func(d interface{}) {
			defer wg.Done()
			results := mapFunc(d)
			mapResults <- results
		}(item)
	}
	
	go func() {
		wg.Wait()
		close(mapResults)
	}()
	
	var allResults []interface{}
	for results := range mapResults {
		allResults = append(allResults, results...)
	}
	
	return reduceFunc(allResults)
}

// StreamProcessor 流式处理器
type StreamProcessor struct {
	bufferSize int
	handlers   []StreamHandler
}

// StreamHandler 流处理函数
type StreamHandler func([]byte) ([]byte, error)

// NewStreamProcessor 创建流处理器
func NewStreamProcessor(bufferSize int) *StreamProcessor {
	return &StreamProcessor{
		bufferSize: bufferSize,
		handlers:   make([]StreamHandler, 0),
	}
}

// AddHandler 添加处理器
func (sp *StreamProcessor) AddHandler(h StreamHandler) {
	sp.handlers = append(sp.handlers, h)
}

// Process 处理数据流
func (sp *StreamProcessor) Process(input <-chan []byte) <-chan []byte {
	output := make(chan []byte, sp.bufferSize)
	
	go func() {
		defer close(output)
		for data := range input {
			result := data
			for _, handler := range sp.handlers {
				if out, err := handler(result); err == nil {
					result = out
				}
			}
			output <- result
		}
	}()
	
	return output
}

// CircuitBreaker 熔断器
type CircuitBreaker struct {
	failures    int32
	threshold   int32
	timeout     time.Duration
	state       int32 // 0: closed, 1: open, 2: half-open
	lastFailure time.Time
	mu          sync.Mutex
}

const (
	StateClosed = iota
	StateOpen
	StateHalfOpen
)

// NewCircuitBreaker 创建熔断器
func NewCircuitBreaker(threshold int32, timeout time.Duration) *CircuitBreaker {
	return &CircuitBreaker{
		threshold: threshold,
		timeout:   timeout,
		state:     StateClosed,
	}
}

// Allow 允许请求
func (cb *CircuitBreaker) Allow() bool {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	switch atomic.LoadInt32(&cb.state) {
	case StateOpen:
		if time.Since(cb.lastFailure) > cb.timeout {
			atomic.StoreInt32(&cb.state, StateHalfOpen)
			return true
		}
		return false
	case StateHalfOpen:
		return true
	default:
		return true
	}
}

// RecordSuccess 记录成功
func (cb *CircuitBreaker) RecordSuccess() {
	atomic.StoreInt32(&cb.state, StateClosed)
	atomic.StoreInt32(&cb.failures, 0)
}

// RecordFailure 记录失败
func (cb *CircuitBreaker) RecordFailure() {
	f := atomic.AddInt32(&cb.failures, 1)
	cb.lastFailure = time.Now()
	if f >= cb.threshold {
		atomic.StoreInt32(&cb.state, StateOpen)
	}
}

// RateLimiter 限流器
type RateLimiter struct {
	rate     int
	burst    int
	tokens   int
	lastTime time.Time
	mu       sync.Mutex
}

// NewRateLimiter 创建限流器
func NewRateLimiter(rate, burst int) *RateLimiter {
	return &RateLimiter{
		rate:   rate,
		burst:  burst,
		tokens: burst,
	}
}

// Allow 允许请求
func (rl *RateLimiter) Allow() bool {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	now := time.Now()
	elapsed := now.Sub(rl.lastTime)
	rl.lastTime = now

	rl.tokens += int(elapsed.Seconds() * float64(rl.rate))
	if rl.tokens > rl.burst {
		rl.tokens = rl.burst
	}

	if rl.tokens > 0 {
		rl.tokens--
		return true
	}
	return false
}

// LoadBalancer 负载均衡器
type LoadBalancer struct {
	backends []Backend
	index    uint32
	mu       sync.RWMutex
}

// Backend 后端服务器
type Backend struct {
	Address   string
	Weight    int
	Healthy   bool
	Failures  int32
}

// NewLoadBalancer 创建负载均衡器
func NewLoadBalancer() *LoadBalancer {
	return &LoadBalancer{
		backends: make([]Backend, 0),
		index:    0,
	}
}

// AddBackend 添加后端
func (lb *LoadBalancer) AddBackend(addr string, weight int) {
	lb.mu.Lock()
	defer lb.mu.Unlock()
	lb.backends = append(lb.backends, Backend{
		Address: addr,
		Weight:  weight,
		Healthy: true,
	})
}

// Next 获取下一个后端
func (lb *LoadBalancer) Next() (string, error) {
	lb.mu.RLock()
	defer lb.mu.RUnlock()

	if len(lb.backends) == 0 {
		return "", fmt.Errorf("no backends available")
	}

	// 轮询算法
	idx := atomic.AddUint32(&lb.index, 1) % uint32(len(lb.backends))
	for i := idx; i < uint32(len(lb.backends)); i++ {
		if lb.backends[i].Healthy {
			return lb.backends[i].Address, nil
		}
	}
	for i := 0; i < idx; i++ {
		if lb.backends[i].Healthy {
			return lb.backends[i].Address, nil
		}
	}

	return "", fmt.Errorf("no healthy backends")
}
