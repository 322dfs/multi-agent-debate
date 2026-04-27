/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // 可爱风亮色搭配
        primary: '#FF6B6B',    // 珊瑚红
        secondary: '#4ECDC4',  // 薄荷绿
        accent: '#FFD166',     // 柠檬黄
        dark: '#292F36',       // 深灰蓝
        light: '#F7FFF7',      // 米白
        success: '#06D6A0',    // 薄荷绿
        warning: '#FFD166',    // 柠檬黄
        error: '#EF476F',      // 珊瑚红
        info: '#118AB2',       // 天蓝
        // 新增亮色
        blue: '#3B82F6',       // 蓝色
        purple: '#8B5CF6',     // 紫色
        pink: '#EC4899',       // 粉色
      },
      fontFamily: {
        sans: ['Poppins', 'sans-serif'],
      },
      animation: {
        'bounce-slow': 'bounce 3s infinite',
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.5s ease-in-out',
        'slide-down': 'slideDown 0.5s ease-in-out',
        'scale-in': 'scaleIn 0.3s ease-in-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
      boxShadow: {
        'cute': '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        'glow': '0 0 15px rgba(78, 205, 196, 0.5)',
        'glow-primary': '0 0 15px rgba(255, 107, 107, 0.5)',
        'glow-secondary': '0 0 15px rgba(78, 205, 196, 0.5)',
        'glow-accent': '0 0 15px rgba(255, 209, 102, 0.5)',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
}
