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

export const openLocationSettings = async () => {
  if (!isNativeAndroid()) {
    return { supported: false, opened: false };
  }

  return BackgroundBroadcast.openLocationSettings();
};

export const openAppSettings = async () => {
  if (!isNativeAndroid()) {
    return { supported: false, opened: false };
  }

  return BackgroundBroadcast.openAppSettings();
};

export const isLocationEnabled = async () => {
  if (!isNativeAndroid()) {
    return { supported: false, enabled: true };
  }

  return BackgroundBroadcast.isLocationEnabled();
};

