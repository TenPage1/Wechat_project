// utils/api.js —— 统一网络请求封装

// 后端地址：云托管公网域名（PC 调试需在开发者工具勾选"不校验合法域名"）
const BASE_URL = 'https://flask-0cc2-314918-11-1410604288.sh.run.tcloudbase.com'
// 本地调试时改回：'http://127.0.0.1:5000'

function request(path, method = 'GET', data = {}) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: BASE_URL + path,
      method,
      data,
      header: { 'content-type': 'application/json' },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else {
          reject(res.data || { msg: 'HTTP ' + res.statusCode })
        }
      },
      fail: (err) => reject(err)
    })
  })
}

// 计算两点距离（米）—— Haversine
function distanceMeters(lng1, lat1, lng2, lat2) {
  const R = 6371000
  const toRad = (d) => (d * Math.PI) / 180
  const dLat = toRad(lat2 - lat1)
  const dLng = toRad(lng2 - lng1)
  const a = Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(a))
}

module.exports = {
  BASE_URL,
  request,
  distanceMeters,
  get: (path, data) => request(path, 'GET', data),
  post: (path, data) => request(path, 'POST', data)
}
