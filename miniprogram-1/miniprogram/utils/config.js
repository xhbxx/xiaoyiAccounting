const BASE_URL = 'http://127.0.0.1:8000'
const IMAGE_BASE_URL = 'https://azsworld.top/uploads'
const token = wx.getStorageSync('token')

function request(url, method = 'GET', data = {}) {
    const token = wx.getStorageSync('token')
    return new Promise((resolve, reject) => {
        wx.request({
            url: BASE_URL + url,
            method,
            data,
            header: token ? {
                Authorization: 'Bearer ' + token
            } : {},

            success: res => {
                if (res.statusCode == 200) {
                    return (resolve(res.data))
                }
                else {
                    reject()
                }

                fail: reject
            }
        })
    })
}
module.exports = { request, BASE_URL,IMAGE_BASE_URL}