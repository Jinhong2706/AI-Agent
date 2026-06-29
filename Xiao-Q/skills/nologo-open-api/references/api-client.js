const axios = require('axios');
const fs = require('fs');
const path = require('path');

const API_BASE = 'https://nologo.code24.top/api/open/parse';
const configPath = path.join(__dirname, 'config.json');

function loadConfig() {
  if (fs.existsSync(configPath)) {
    return JSON.parse(fs.readFileSync(configPath, 'utf8'));
  }
  return { token: '' };
}

function setToken(token) {
  const config = loadConfig();
  config.token = token;
  fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
  console.log('Token saved:', token);
}

function getToken() {
  return loadConfig().token;
}

async function parseUrl(url) {
  const token = getToken();
  if (!token) {
    throw new Error('请先设置Token: setToken("your-token-here")');
  }

  const encodedUrl = encodeURIComponent(url);
  const apiUrl = `${API_BASE}?url=${encodedUrl}`;

  const response = await axios.get(apiUrl, {
    headers: { 'Authorization': token }
  });

  return response.data;
}

function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  if (command === 'set-token') {
    setToken(args[1]);
  } else if (command === 'parse') {
    parseUrl(args[1]).then(console.log).catch(console.error);
  } else {
    console.log('用法:');
    console.log('  node api-client.js set-token <token>  设置Token');
    console.log('  node api-client.js parse <url>   解析链接');
  }
}

if (require.main === module) {
  main();
}

module.exports = { setToken, getToken, parseUrl };