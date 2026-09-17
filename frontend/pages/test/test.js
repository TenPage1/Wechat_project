// pages/test/test.js —— 前后端通信测试页（直连公网域名）
const BASE_URL = 'https://flask-0cc2-314918-11-1410604288.sh.run.tcloudbase.com'

Page({
  data: {
    result: ''
  },

  // 测试 1：调用 /hello（GET）
  testHello() {
    this.request('/hello', 'GET', { name: '小程序' })
  },

  // 测试 2：保存数据（POST）
  testSave() {
    this.request('/save', 'POST', {
      openid: 'test-user',
      longitude: '119',
      latitude: '33'
    })
  },

  // 测试 3：读取数据（GET）
  testGet() {
    this.request('/get', 'GET', { openid: 'test-user' })
  },

  // 封装：wx.request 直连公网域名
  request(path, method, data) {
    wx.showLoading({ title: '请求中' })
    wx.request({
      url: BASE_URL + path,
      method,
      header: { 'content-type': 'application/json' },
      data,
      success: (res) => {
        wx.hideLoading()
        console.log('后端返回：', res.data, '状态码：', res.statusCode)
        this.setData({
          result: 'HTTP ' + res.statusCode + '\n' + JSON.stringify(res.data, null, 2)
        })
        wx.showToast({ title: '请求成功', icon: 'success' })
      },
      fail: (err) => {
        wx.hideLoading()
        console.error('请求失败：', err)
        this.setData({ result: '请求失败：\n' + JSON.stringify(err, null, 2) })
        wx.showModal({
          title: '请求失败',
          content: (err && err.errMsg) || JSON.stringify(err),
          showCancel: false
        })
      }
    })
  }
})
