import { createApp } from 'vue'
import AGContactListPage from 'AGContactListPage.vue'

frappe.ui.setup_ag_contact_list = function (wrapper) {
  const app = createApp(AGContactListPage)
  app.mount(wrapper.get(0))
  return app
}
