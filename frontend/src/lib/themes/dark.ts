/**
 * Dark theme definition
 */

import type { PresetTheme } from '../types/themes.js'

export const darkTheme: PresetTheme = {
  name: 'dark',
  displayName: 'Dark Theme',
  description: 'Comfortable dark theme for low-light environments',
  config: {
    theme: 'dark',
    colors: {
      primary: '#60a5fa',
      secondary: '#9ca3af',
      background: '#111827',
      surface: '#1f2937',
      text: '#f9fafb',
      textSecondary: '#9ca3af',
      border: '#374151',
      hover: '#374151',
      selected: '#1e40af',

      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      info: '#06b6d4',

      surfaceVariant: '#374151',
      surfaceHover: '#4b5563',
      surfaceSelected: '#1e40af'
    },
    density: 'comfortable',
    borderRadius: 'medium',
    fontSize: 'medium',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',

    table: {
      stripedRows: true,
      hoverEffect: true,
      stickyHeader: true,
      borderStyle: 'light',
      headerStyle: 'minimal',
      rowHeight: 'comfortable',
      showBorders: true,
      alternatingBackground: true
    },

    cards: {
      shadow: 'medium',
      border: true,
      rounded: true,
      hoverEffect: 'glow',
      padding: 'medium'
    },

    grid: {
      gap: 'medium',
      cardSize: 'medium',
      aspectRatio: '1:1'
    },

    list: {
      density: 'comfortable',
      separator: true,
      thumbnailSize: 'medium'
    }
  }
}