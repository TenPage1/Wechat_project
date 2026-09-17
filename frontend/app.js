// app.js
App({
  globalData: {
    openid: ''
  },

  onLaunch() {
    wx.cloud.init({
      env: "prod-d4g787qk771f33524",
      traceUser: true
    })
  }
})

