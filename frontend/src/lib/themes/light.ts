/**
 * Light theme definition
 */

import type { PresetTheme } from '../types/themes.js'

export const lightTheme: PresetTheme = {
  name: 'light',
  displayName: 'Light Theme',
  description: 'Clean and bright theme optimized for daylight use',
  config: {
    theme: 'light',
    colors: {
      primary: '#3b82f6',
      secondary: '#6b7280',
      background: '#ffffff',
      surface: '#f9fafb',
      text: '#111827',
      textSecondary: '#6b7280',
      border: '#e5e7eb',
      hover: '#f3f4f6',
      selected: '#dbeafe',

      success: '#059669',
      warning: '#d97706',
      error: '#dc2626',
      info: '#0284c7',

      surfaceVariant: '#f3f4f6',
      surfaceHover: '#e5e7eb',
      surfaceSelected: '#dbeafe'
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
      shadow: 'small',
      border: true,
      rounded: true,
      hoverEffect: 'lift',
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