<template>
  <!-- Items card — no bottom border/radius, connects visually to totals below -->
  <div class="card" style="margin-bottom: 0; border-bottom-left-radius: 0; border-bottom-right-radius: 0; border-bottom: none">
    <div class="card-header">Items</div>
    <div class="items-wrap">
      <table class="itbl">
        <thead>
          <tr>
            <th style="width: 30px">#</th>
            <th>Description</th>
            <th style="width: 90px">Purity</th>
            <th style="width: 130px">Gross Wt (g)</th>
            <th style="width: 90px; text-align: left">Net Wt (g)</th>
            <th style="width: 110px" class="r">Rate (RM/g)</th>
            <th style="width: 32px"></th>
            <th style="width: 120px" class="r">Amount (RM)</th>
            <th style="width: 60px"></th>
          </tr>
        </thead>
        <tbody>
          <ItemRow
            v-for="(item, idx) in gb.items.value"
            :key="item.id"
            :item="item"
            :idx="idx"
            :isLastAdded="gb.lastAddedId.value === item.id"
          />
        </tbody>
        <!-- Add Item in tfoot — matches original exactly -->
        <tfoot>
          <tr>
            <td colspan="9">
              <button class="add-item-btn" @click="gb.addItem()">＋ Add Item</button>
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  </div>

  <!-- Totals — separate connected div below items card (no top border-radius) -->
  <div style="background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); margin-bottom: 12px; box-shadow: var(--shadow); border-top-left-radius: 0; border-top-right-radius: 0; border-top: none">
    <div class="totals-section">
      <div class="totals-inner">
        <div class="totals-right-block">
          <div class="tot-row">
            <span class="lbl">Total Gross Weight</span>
            <span class="val">{{ fmtWt(gb.totGross.value) }}</span>
          </div>
          <div class="tot-row">
            <span class="lbl">Total Net Weight</span>
            <span class="val">{{ fmtWt(gb.totNet.value) }}</span>
          </div>
          <div class="tot-row">
            <span class="lbl">Total Amount</span>
            <span class="val">RM {{ fmtRM(gb.totAmt.value) }}</span>
          </div>
          <div class="tot-divider"></div>
          <div class="tot-controls">
            <div class="lc">
              <input type="checkbox" id="rndChk" v-model="gb.round.value" />
              <label for="rndChk" style="cursor: pointer">Apply Rounding</label>
              <span class="round-hint">{{ gb.roundHint.value }}</span>
            </div>
            <div class="rc">
              <label>Discount (RM)</label>
              <input type="text" class="disc-input" placeholder="0.00"
                :value="gb.discDisp.value"
                @focus="e => gb.discDisp.value = e.target.value.replace(/,/g, '')"
                @input="e => { gb.discDisp.value = e.target.value; gb.disc.value = e.target.value }"
                @blur="e => {
                  const v = parseFloat(e.target.value.replace(/,/g, ''))
                  gb.disc.value = isNaN(v) ? '' : String(v)
                  gb.discDisp.value = isNaN(v) ? '' : fmtRM(v)
                }"
                @keydown.enter="e => e.target.blur()"
              />
            </div>
          </div>
          <div class="tot-divider"></div>
          <div class="grand-row">
            <span class="lbl">Grand Total</span>
            <span class="val">RM {{ fmtRM(gb.gt.value) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { inject } from 'vue'
import { fmtRM, fmtWt } from '../../../utils/formatters.js'
import ItemRow from './ItemRow.vue'

const gb = inject('gb')
</script>
