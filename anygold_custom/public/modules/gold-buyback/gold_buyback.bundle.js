import { createApp } from 'vue'
import GoldBuybackPage from 'GoldBuybackPage.vue'

frappe.ui.setup_gold_buyback = function(wrapper) {
    
    const app = createApp(GoldBuybackPage)
    app.mount(wrapper.get(0))
    return app
  }