import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.patient.trend',
  appName: '报告管理',
  webDir: 'dist',
  bundledWebRuntime: false,
  // 允许 HTTP Cleartext（访问后端 API）
  server: {
    cleartext: true,
  },
  android: {
    // 允许 Android 使用 HTTP
    allowMixedContent: true,
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
      backgroundColor: '#FFFFFFFF',
      showSpinner: true,
      spinnerColor: '#6366f1',
    },
    Keyboard: {
      resize: 'body',
    },
  },
};

export default config;
