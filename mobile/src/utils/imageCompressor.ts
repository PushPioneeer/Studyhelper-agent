/**
 * 图片压缩工具
 * 用于压缩图片后再上传，减少传输时间和 API 处理时间
 */

import * as ImagePicker from 'expo-image-picker';

/**
 * 压缩图片
 * @param uri 图片 URI
 * @param options 压缩选项
 * @returns 压缩后的图片 URI
 */
export const compressImage = async (
  uri: string,
  options: {
    maxWidth?: number;
    maxHeight?: number;
    quality?: number;
  } = {}
): Promise<string> => {
  const {
    maxWidth = 800,
    maxHeight = 600,
    quality = 0.7,
  } = options;

  try {
    // 使用 expo-image-picker 的压缩功能
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [4, 3],
      quality: quality,
      base64: false,
    });

    if (!result.canceled && result.assets && result.assets.length > 0) {
      return result.assets[0].uri;
    }

    // 如果是拍照，使用拍照的结果
    return uri;
  } catch (error) {
    console.error('图片压缩失败:', error);
    return uri; // 压缩失败，返回原图
  }
};

/**
 * 拍照并压缩
 * @param options 压缩选项
 * @returns 压缩后的图片 URI
 */
export const takePhotoAndCompress = async (
  options: {
    maxWidth?: number;
    maxHeight?: number;
    quality?: number;
  } = {}
): Promise<string | null> => {
  try {
    // 请求相机权限
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      alert('需要相机权限才能拍照');
      return null;
    }

    // 拍照
    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [4, 3],
      quality: options.quality || 0.7,
      base64: false,
    });

    if (!result.canceled && result.assets && result.assets.length > 0) {
      return result.assets[0].uri;
    }

    return null;
  } catch (error) {
    console.error('拍照失败:', error);
    return null;
  }
};

/**
 * 从相册选择并压缩
 * @param options 压缩选项
 * @returns 压缩后的图片 URI
 */
export const pickImageAndCompress = async (
  options: {
    maxWidth?: number;
    maxHeight?: number;
    quality?: number;
  } = {}
): Promise<string | null> => {
  try {
    // 请求相册权限
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      alert('需要相册权限才能选择图片');
      return null;
    }

    // 选择图片
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [4, 3],
      quality: options.quality || 0.7,
      base64: false,
    });

    if (!result.canceled && result.assets && result.assets.length > 0) {
      return result.assets[0].uri;
    }

    return null;
  } catch (error) {
    console.error('选择图片失败:', error);
    return null;
  }
};

/**
 * 获取图片大小（字节）
 * @param uri 图片 URI
 * @returns 图片大小（字节）
 */
export const getImageSize = async (uri: string): Promise<number> => {
  try {
    const response = await fetch(uri);
    const blob = await response.blob();
    return blob.size;
  } catch (error) {
    console.error('获取图片大小失败:', error);
    return 0;
  }
};

/**
 * 格式化文件大小
 * @param bytes 字节数
 * @returns 格式化后的大小字符串
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
};
