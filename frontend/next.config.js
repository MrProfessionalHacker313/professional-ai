/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  compiler: {
    removeConsole: {
      exclude: ['error', 'warn'],
    },
  },
  ...(process.env.NODE_ENV !== 'development' ? { output: 'export' } : {}),
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    domains: ['avatars.githubusercontent.com', 'lh3.googleusercontent.com', 'platform-lookaside.fbsbx.com'],
    unoptimized: true,
  },
  webpack: (config, { isServer, dev }) => {
    // Ignore native Node modules that transformers.js pulls in.
    // We use the browser/WASM build of onnxruntime, not the Node native build.
    config.externals = config.externals || [];
    config.externals.push({
      'onnxruntime-node': 'commonjs onnxruntime-node',
      sharp: 'commonjs sharp',
    });

    // Ignore .node binary files (native addons) from webpack parsing
    config.module.rules.push({
      test: /\.node$/,
      use: 'ignore-loader',
    });

    return config;
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/:path*`,
      },
    ];
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          // Security headers
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'X-Modified',
            value: 'true'
          },
          // Preconnect to API and CDN
          {
            key: 'Link',
            value: [
              `<${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}>; rel=preconnect; crossorigin`,
              'https://cdn.professional-ai.com; rel=preconnect; crossorigin',
              'https://fonts.googleapis.com; rel=preconnect; crossorigin',
              'https://fonts.gstatic.com; rel=preconnect; crossorigin',
            ].join(', ')
          },
        ],
      },
      {
        // Cache static assets aggressively (1 year, immutable)
        source: '/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        // Cache images for 1 day
        source: '/_next/image/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=86400',
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
