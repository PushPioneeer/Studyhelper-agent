/**
 * 流式请求 Hook
 * 使用 EventSource 实现真正的实时流式输出
 */

import { useState, useEffect, useCallback, useRef } from 'react';

interface UseStreamingOptions {
  /** 是否自动连接 */
  autoConnect?: boolean;
  /** 重试次数 */
  maxRetries?: number;
  /** 重试间隔（毫秒） */
  retryInterval?: number;
  /** 超时时间（毫秒） */
  timeout?: number;
}

interface UseStreamingReturn<T = any> {
  /** 接收到的数据 */
  data: string;
  /** 是否正在加载 */
  loading: boolean;
  /** 错误信息 */
  error: string | null;
  /** 是否完成 */
  done: boolean;
  /** 连接 */
  connect: (url: string, options?: RequestInit) => void;
  /** 关闭连接 */
  close: () => void;
  /** 重置状态 */
  reset: () => void;
}

/**
 * 流式请求 Hook
 * @param url SSE 端点 URL
 * @param options 配置选项
 * @returns 流式请求状态和方法
 */
export const useStreaming = <T = any>(
  url?: string,
  options: UseStreamingOptions = {}
): UseStreamingReturn<T> => {
  const {
    autoConnect = false,
    maxRetries = 3,
    retryInterval = 3000,
    timeout = 60000,
  } = options;

  const [data, setData] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const eventSourceRef = useRef<EventSource | null>(null);
  const retryCountRef = useRef(0);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  /** 关闭连接 */
  const close = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  /** 重置状态 */
  const reset = useCallback(() => {
    close();
    setData('');
    setLoading(false);
    setError(null);
    setDone(false);
    retryCountRef.current = 0;
  }, [close]);

  /** 连接 SSE */
  const connect = useCallback(
    (connectUrl?: string, fetchOptions?: RequestInit) => {
      const targetUrl = connectUrl || url;
      if (!targetUrl) {
        setError('URL 不能为空');
        return;
      }

      // 重置状态
      reset();
      setLoading(true);

      try {
        // 创建 EventSource
        const eventSource = new EventSource(targetUrl);
        eventSourceRef.current = eventSource;

        // 设置超时
        timeoutRef.current = setTimeout(() => {
          close();
          setError('请求超时');
          setLoading(false);
        }, timeout);

        // 连接成功
        eventSource.onopen = () => {
          console.log('SSE 连接已建立');
          retryCountRef.current = 0;
        };

        // 接收消息
        eventSource.onmessage = (event) => {
          try {
            const parsed = JSON.parse(event.data);
            
            if (parsed.chunk) {
              // 追加 chunk
              setData((prev) => prev + parsed.chunk);
            }

            if (parsed.done) {
              // 完成
              setDone(true);
              setLoading(false);
              close();
            }

            if (parsed.error) {
              // 错误
              setError(parsed.error);
              setLoading(false);
              close();
            }
          } catch (err) {
            console.error('解析 SSE 消息失败:', err);
            setError('数据解析失败');
            setLoading(false);
          }
        };

        // 错误处理
        eventSource.onerror = (err) => {
          console.error('SSE 连接错误:', err);
          
          // 检查是否需要重试
          if (retryCountRef.current < maxRetries) {
            retryCountRef.current += 1;
            console.log(`重试 ${retryCountRef.current}/${maxRetries}`);
            
            // 延迟重试
            setTimeout(() => {
              connect(targetUrl, fetchOptions);
            }, retryInterval);
          } else {
            setError('连接失败，请检查网络');
            setLoading(false);
            close();
          }
        };
      } catch (err) {
        console.error('创建 SSE 连接失败:', err);
        setError('无法建立连接');
        setLoading(false);
      }
    },
    [url, reset, close, maxRetries, retryInterval, timeout]
  );

  // 自动连接
  useEffect(() => {
    if (autoConnect && url) {
      connect(url);
    }

    // 清理
    return () => {
      close();
    };
  }, [autoConnect, url, connect, close]);

  return {
    data,
    loading,
    error,
    done,
    connect,
    close,
    reset,
  };
};

/**
 * 使用 fetch 实现的流式请求（备用方案）
 * 适用于不支持 EventSource 的场景
 */
export const useFetchStreaming = <T = any>(
  url?: string,
  options: RequestInit & {
    autoConnect?: boolean;
  } = {}
): UseStreamingReturn<T> => {
  const { autoConnect = false, ...fetchOptions } = options;

  const [data, setData] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const abortControllerRef = useRef<AbortController | null>(null);

  /** 关闭连接 */
  const close = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  }, []);

  /** 重置状态 */
  const reset = useCallback(() => {
    close();
    setData('');
    setLoading(false);
    setError(null);
    setDone(false);
  }, [close]);

  /** 连接流式 */
  const connect = useCallback(
    async (connectUrl?: string, overrideOptions?: RequestInit) => {
      const targetUrl = connectUrl || url;
      if (!targetUrl) {
        setError('URL 不能为空');
        return;
      }

      reset();
      setLoading(true);

      try {
        const controller = new AbortController();
        abortControllerRef.current = controller;

        const response = await fetch(targetUrl, {
          ...fetchOptions,
          ...overrideOptions,
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP 错误：${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('无法获取响应流');
        }

        const decoder = new TextDecoder('utf-8');

        while (true) {
          const { done: streamDone, value } = await reader.read();

          if (streamDone) {
            setDone(true);
            setLoading(false);
            break;
          }

          const chunk = decoder.decode(value, { stream: true });
          
          // 解析 SSE 格式
          const lines = chunk.split('\n');
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.slice(6);
              try {
                const parsed = JSON.parse(dataStr);
                if (parsed.chunk) {
                  setData((prev) => prev + parsed.chunk);
                }
                if (parsed.done) {
                  setDone(true);
                  setLoading(false);
                }
              } catch {
                // 非 JSON 格式，直接使用
                setData((prev) => prev + dataStr);
              }
            }
          }
        }
      } catch (err: any) {
        if (err.name === 'AbortError') {
          console.log('流式请求已取消');
        } else {
          console.error('流式请求失败:', err);
          setError(err.message || '请求失败');
          setLoading(false);
        }
      }
    },
    [url, fetchOptions, reset]
  );

  // 自动连接
  useEffect(() => {
    if (autoConnect && url) {
      connect(url);
    }

    return () => {
      close();
    };
  }, [autoConnect, url, connect, close]);

  return {
    data,
    loading,
    error,
    done,
    connect,
    close,
    reset,
  };
};
