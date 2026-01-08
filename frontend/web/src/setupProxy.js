const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app, server) {
  // Используем setupMiddlewares для новой версии webpack-dev-server
  if (app.get && typeof app.use === 'function') {
    // Proxy для обычных HTTP запросов и WebSocket
    const apiProxy = createProxyMiddleware({
      target: 'http://localhost:8000',
      changeOrigin: true,
      secure: false,
      ws: true,  // Включаем поддержку WebSocket
      logLevel: 'debug',
      onProxyReqWs: (proxyReq, req, socket) => {
        console.log('WebSocket проксирование:', req.url);
      },
      onError: (err, req, res) => {
        console.error('Ошибка прокси:', err);
      }
    });
    
    app.use('/api', apiProxy);
    
    // Настраиваем WebSocket прокси для сервера
    if (server) {
      server.on('upgrade', apiProxy.upgrade);
    }
  }
};

