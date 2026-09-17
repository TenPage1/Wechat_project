// utils/api.js —— 统一网络请求封装

// 后端地址：本地调试
const BASE_URL = 'http://127.0.0.1:5000'
// 上线后改回云托管域名：'https://flask-0cc2-314918-11-1410604288.sh.run.tcloudbase.com'

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
