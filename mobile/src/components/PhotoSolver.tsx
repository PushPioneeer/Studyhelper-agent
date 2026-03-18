/**
 * 拍照解题组件 - 优化版本
 * 使用图片压缩和流式输出
 */

import React, { useState } from 'react';
import { View, Text, TouchableOpacity, Image, ActivityIndicator, StyleSheet } from 'react-native';
import { takePhotoAndCompress, formatFileSize } from '../utils/imageCompressor';
import { useStreaming } from '../hooks/useStreaming';

interface PhotoSolverProps {
  /** 上传 API 端点 */
  uploadUrl: string;
  /** 流式 API 端点 */
  streamUrl: string;
  /** Token */
  token: string;
  /** 解题完成回调 */
  onSolved?: (result: any) => void;
}

export const PhotoSolver: React.FC<PhotoSolverProps> = ({
  uploadUrl,
  streamUrl,
  token,
  onSolved,
}) => {
  const [imageUri, setImageUri] = useState<string | null>(null);
  const [imageSize, setImageSize] = useState<number>(0);
  const [uploading, setUploading] = useState(false);

  // 使用流式 Hook
  const {
    data: solution,
    loading: streaming,
    error: streamError,
    done: streamDone,
    connect: connectStream,
    reset: resetStream,
  } = useStreaming();

  /** 拍照并上传 */
  const handleTakePhoto = async () => {
    try {
      // 拍照并自动压缩
      const compressedUri = await takePhotoAndCompress({
        maxWidth: 800,
        maxHeight: 600,
        quality: 0.7,
      });

      if (!compressedUri) {
        alert('拍照失败');
        return;
      }

      setImageUri(compressedUri);
      
      // 获取图片大小
      const response = await fetch(compressedUri);
      const blob = await response.blob();
      setImageSize(blob.size);

      // 上传
      await uploadImage(compressedUri);
    } catch (error) {
      console.error('拍照失败:', error);
      alert('拍照失败，请重试');
    }
  };

  /** 上传图片 */
  const uploadImage = async (uri: string) => {
    setUploading(true);
    resetStream();

    try {
      const formData = new FormData();
      
      // @ts-ignore
      formData.append('images', {
        uri,
        type: 'image/jpeg',
        name: 'question.jpg',
      } as any);

      formData.append('subject', 'math');

      // 先上传获取题目 ID
      const uploadResponse = await fetch(uploadUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (!uploadResponse.ok) {
        throw new Error('上传失败');
      }

      const result = await uploadResponse.json();
      const questionId = result.id;

      // 连接到流式接口
      const streamEndpoint = `${streamUrl}/${questionId}/stream`;
      connectStream(streamEndpoint);

    } catch (error: any) {
      console.error('上传失败:', error);
      alert(`上传失败：${error.message}`);
    } finally {
      setUploading(false);
    }
  };

  /** 解题完成处理 */
  React.useEffect(() => {
    if (streamDone && solution) {
      console.log('解题完成:', solution);
      onSolved?.({
        questionId: null,
        solution,
        imageUri,
      });
    }
  }, [streamDone, solution, onSolved, imageUri]);

  return (
    <View style={styles.container}>
      {/* 拍照按钮 */}
      <TouchableOpacity
        style={styles.cameraButton}
        onPress={handleTakePhoto}
        disabled={uploading || streaming}
      >
        <Text style={styles.cameraButtonText}>📷 拍照解题</Text>
      </TouchableOpacity>

      {/* 图片预览 */}
      {imageUri && (
        <View style={styles.imageContainer}>
          <Image source={{ uri: imageUri }} style={styles.image} />
          <Text style={styles.imageSize}>
            图片大小：{formatFileSize(imageSize)}
          </Text>
        </View>
      )}

      {/* 上传中 */}
      {uploading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>正在上传...</Text>
        </View>
      )}

      {/* 流式输出中 */}
      {streaming && (
        <View style={styles.streamingContainer}>
          <ActivityIndicator size="small" color="#007AFF" />
          <Text style={styles.streamingText}>AI 正在解题中...</Text>
        </View>
      )}

      {/* 解题结果 */}
      {solution && (
        <View style={styles.solutionContainer}>
          <Text style={styles.solutionTitle}>解题过程：</Text>
          <Text style={styles.solutionText}>{solution}</Text>
        </View>
      )}

      {/* 错误提示 */}
      {streamError && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>❌ {streamError}</Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
  cameraButton: {
    backgroundColor: '#007AFF',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 16,
  },
  cameraButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  imageContainer: {
    marginBottom: 16,
  },
  image: {
    width: '100%',
    height: 300,
    borderRadius: 8,
  },
  imageSize: {
    marginTop: 8,
    color: '#666',
    fontSize: 14,
  },
  loadingContainer: {
    alignItems: 'center',
    padding: 16,
  },
  loadingText: {
    marginTop: 8,
    color: '#666',
    fontSize: 16,
  },
  streamingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
  },
  streamingText: {
    marginLeft: 8,
    color: '#666',
    fontSize: 16,
  },
  solutionContainer: {
    backgroundColor: '#f9f9f9',
    padding: 16,
    borderRadius: 8,
    marginTop: 16,
  },
  solutionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  solutionText: {
    fontSize: 15,
    lineHeight: 22,
    color: '#333',
  },
  errorContainer: {
    backgroundColor: '#ffe6e6',
    padding: 12,
    borderRadius: 8,
    marginTop: 16,
  },
  errorText: {
    color: '#ff3333',
    fontSize: 15,
  },
});
