// pages/profile/profile.js —— 个人中心
const api = require('../../utils/api.js')

Page({
  data: {
    openid: '',
    history: [],
    feedback: ''
  },

  onShow() {
    const openid = wx.getStorageSync('openid') || ''
    this.setData({ openid })
    if (openid) this.loadHistory()
  },

  loadHistory() {
    api.get('/api/history', { openid: this.data.openid }).then((r) => {
      if (r.code === 0) this.setData({ history: r.data || [] })
    }).catch((e) => console.error('拉取历史失败', e))
  },

  onFeedbackInput(e) {
    this.setData({ feedback: e.detail.value })
  },

  submitFeedback() {
    const content = (this.data.feedback || '').trim()
    if (!content) {
      wx.showToast({ title: '请输入建议内容', icon: 'none' })
      return
    }
    api.post('/api/feedback', { openid: this.data.openid, content }).then((r) => {
      if (r.code === 0) {
        wx.showToast({ title: '提交成功', icon: 'success' })
        this.setData({ feedback: '' })
      } else {
        wx.showToast({ title: r.msg || '提交失败', icon: 'none' })
      }
    }).catch(() => wx.showToast({ title: '提交失败', icon: 'none' }))
  }
})
