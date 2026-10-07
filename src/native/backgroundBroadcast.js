import { Capacitor, registerPlugin } from '@capacitor/core';

const BackgroundBroadcast = registerPlugin('BackgroundBroadcast');

export const isNativeAndroid = () => Capacitor.isNativePlatform() && Capacitor.getPlatform() === 'android';

export const startBackgroundBroadcast = async (options) => {
  if (!isNativeAndroid()) {
    return { supported: false, started: false };
  }

  return BackgroundBroadcast.start(options);
};

export const stopBackgroundBroadcast = async () => {
  if (!isNativeAndroid()) {
    return { supported: false, stopped: false };
  }

  return BackgroundBroadcast.stop();
};

export const isBackgroundBroadcastRunning = async () => {
  if (!isNativeAndroid()) {
    return { supported: false, running: false };
  }

  return BackgroundBroadcast.isRunning();
};

export const getBackgroundBroadcastStatus = async () => {
  if (!isNativeAndroid()) {
    return { supported: false, running: false, speed: 0 };
  }

  return BackgroundBroadcast.getStatus();
};
