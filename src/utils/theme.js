import { StatusBar, Style } from '@capacitor/status-bar';
import { Capacitor } from '@capacitor/core';

/**
 * Gets the current theme ('dark' or 'light')
 */
export function getSavedTheme() {
  try {
    const saved = localStorage.getItem('transit_theme');
    if (saved === 'dark' || saved === 'light') return saved;
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
      return 'light';
    }
  } catch (e) {}
  return 'dark';
}

/**
 * Applies the theme to the document HTML element, meta tags, and mobile native status bar
 */
export async function applyTheme(theme = 'dark') {
  const isDark = theme === 'dark';
  const root = document.documentElement;

  if (isDark) {
    root.classList.add('dark');
    root.classList.remove('light');
  } else {
    root.classList.add('light');
    root.classList.remove('dark');
  }

  // Update theme-color meta tag for mobile browsers and PWA
  const bgColor = isDark ? '#0b1120' : '#ffffff';
  let metaTheme = document.querySelector('meta[name="theme-color"]');
  if (!metaTheme) {
    metaTheme = document.createElement('meta');
    metaTheme.name = 'theme-color';
    document.head.appendChild(metaTheme);
  }
  metaTheme.setAttribute('content', bgColor);

  // Update native Capacitor Android / iOS status bar
  if (Capacitor.isNativePlatform()) {
    try {
      await StatusBar.setBackgroundColor({ color: bgColor });
      // Style.Dark has light text (for dark backgrounds)
      // Style.Light has dark text (for light backgrounds)
      await StatusBar.setStyle({ style: isDark ? Style.Dark : Style.Light });
    } catch (err) {
      console.warn('Native status bar sync error:', err);
    }
  }

  try {
    localStorage.setItem('transit_theme', theme);
  } catch (e) {}
}
