Component({
  data: {
      active:0,
      hidden:false,
      list:[
        "/pages/detail/detail",
        "/pages/chart/chart",
        "/pages/bill/bill",      
        "/pages/discover/discover",
        "/pages/profile/profile"
      ]
    },
  methods: {
    switchTab(e){
      const index =e.currentTarget.dataset.index;
      const url = this.data.list[index];
      if(index===this.data.active) return;  
      wx.switchTab({url});
    }
   }
})