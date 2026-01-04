/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './src/**/*.{vue,js,ts,jsx,tsx,html}',
  ],
  theme: {
    extend: {
      colors: {
        // Claude 主色 - 珊瑚橙
        claude: {
          50: '#FEF7F4',
          100: '#FDEBE4',
          200: '#FBDACB',
          300: '#F5B89A',
          400: '#E8956A',
          500: '#DA7756',  // 主色
          600: '#C5623E',
          700: '#A54D32',
          800: '#863E2A',
          900: '#6E3425',
        },
        // 侧边栏背景 - 橘黄色
        sidebar: {
          DEFAULT: '#FBEECB',
          hover: 'rgba(218,119,86,0.1)',
          active: '#DA7756',
          border: '#E8DDB8',
        },
        // 主内容区背景
        content: {
          DEFAULT: '#FFFFFF',
          card: '#FFFFFF',
        },
        // 文字色 - 深棕色调
        text: {
          primary: '#5D4E37',    // 主文字
          secondary: '#8B7355',  // 次要文字
          muted: '#A89880',      // 淡化文字
          light: '#C4B59B',      // 更淡文字
        },
        // 边框色
        border: {
          DEFAULT: '#E8DDB8',
          light: '#F0E6C8',
          dark: '#D4C9A8',
        },
      },
      fontFamily: {
        sans: ['Söhne', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'Noto Sans SC', 'sans-serif'],
      },
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.25rem',
      }
    }
  },
  plugins: [],
}
