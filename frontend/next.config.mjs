/** @type {import('next').NextConfig} */
const nextConfig = {};


export default {
    webpack: (config, { dev }) => {
      if (dev) {
        config.cache = false; // 開発時にキャッシュを無効にする
      }
      return config;
    },
  };
  