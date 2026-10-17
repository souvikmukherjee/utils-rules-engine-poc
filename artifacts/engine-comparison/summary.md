# Zen vs Kogito — 100 complex case comparison

- Cases: **100**
- Decision agreement: **68/100 (68.0%)**
- Exact lounge-class agreement: **25/100 (25.0%)**
- Companion agreement: **60/100 (60.0%)**
- Full parity (decision+lounge+companions+benefits): **21/100 (21.0%)**
- Engine errors: **0**

## Contingency (Zen ↓ / Kogito →)

```
{
  "inconclusive": {
    "inconclusive": 18,
    "allow": 12
  },
  "allow": {
    "inconclusive": 15,
    "allow": 45,
    "deny": 3
  },
  "deny": {
    "deny": 5,
    "inconclusive": 1,
    "allow": 1
  }
}
```

## Decision mismatches (32)

- `C002` matrix:bronze+business: zen=allow kogito=inconclusive rules zen=['bronze-business-qantas_club'] kogito=[]
- `C003` matrix:bronze+first: zen=allow kogito=inconclusive rules zen=['bronze-first-first'] kogito=[]
- `C005` matrix:silver+premium_economy: zen=allow kogito=inconclusive rules zen=['silver-premium_economy-qantas_club'] kogito=[]
- `C006` matrix:silver+business: zen=allow kogito=inconclusive rules zen=['silver-business-business'] kogito=[]
- `C007` matrix:silver+first: zen=allow kogito=inconclusive rules zen=['silver-first-first'] kogito=[]
- `C016` matrix:platinum_one+economy: zen=allow kogito=inconclusive rules zen=['platinum-one-companion', 'platinum_one-economy-chairmans'] kogito=[]
- `C017` matrix:platinum_one+premium_economy: zen=allow kogito=inconclusive rules zen=['platinum-one-companion', 'platinum_one-premium_economy-chairmans'] kogito=[]
- `C018` matrix:platinum_one+business: zen=allow kogito=inconclusive rules zen=['platinum-one-companion', 'platinum_one-business-chairmans'] kogito=[]
- `C019` matrix:platinum_one+first: zen=allow kogito=inconclusive rules zen=['platinum-one-companion', 'platinum_one-first-chairmans'] kogito=[]
- `C020` matrix:diamond+economy: zen=inconclusive kogito=allow rules zen=[] kogito=['companion-plus-one', 'tier-gold-lounge']
- `C021` matrix:diamond+premium_economy: zen=inconclusive kogito=allow rules zen=[] kogito=['companion-plus-one', 'tier-gold-lounge']
- `C022` matrix:diamond+business: zen=inconclusive kogito=allow rules zen=[] kogito=['companion-plus-one', 'tier-gold-lounge']
- `C023` matrix:diamond+first: zen=inconclusive kogito=allow rules zen=[] kogito=['companion-plus-one', 'tier-gold-lounge']
- `C032` default_cabin:diamond: zen=inconclusive kogito=allow rules zen=[] kogito=['companion-plus-one', 'tier-gold-lounge']
- `C034` default_cabin:platinum_one: zen=allow kogito=inconclusive rules zen=['platinum-one-companion', 'platinum_one-economy-chairmans'] kogito=[]
- `C056` peak_bronze_economy: zen=deny kogito=inconclusive rules zen=['seasonal-peak-deny-low-tier'] kogito=[]
- `C057` peak_silver_business: zen=allow kogito=deny rules zen=['silver-business-business'] kogito=['seasonal-peak-deny-silver']
- `C060` peak_bronze_partner: zen=deny kogito=allow rules zen=['partner-elite-club', 'seasonal-peak-deny-low-tier'] kogito=['partner-elite-access']
- `C065` peak_diamond: zen=inconclusive kogito=allow rules zen=[] kogito=['companion-plus-one', 'tier-gold-lounge']
- `C066` peak_silver_prem: zen=allow kogito=deny rules zen=['silver-premium_economy-qantas_club'] kogito=['seasonal-peak-deny-silver']
- `C068` peak_bronze_first: zen=allow kogito=inconclusive rules zen=['bronze-first-first'] kogito=[]
- `C071` comp_on_bronze: zen=inconclusive kogito=allow rules zen=[] kogito=['companion-plus-one']
- `C076` comp_off_p1: zen=allow kogito=inconclusive rules zen=['platinum-one-companion', 'platinum_one-economy-chairmans'] kogito=[]
- `C078` comp_off_diamond: zen=inconclusive kogito=allow rules zen=[] kogito=['companion-plus-one', 'tier-gold-lounge']
- `C079` comp_on_diamond: zen=inconclusive kogito=allow rules zen=[] kogito=['companion-plus-one', 'tier-gold-lounge']
- `C080` comp_on_unknown: zen=inconclusive kogito=allow rules zen=[] kogito=['companion-plus-one']
- `C082` comp_on_silver_econ: zen=inconclusive kogito=allow rules zen=[] kogito=['companion-plus-one']
- `C084` comp_off_p1_biz: zen=allow kogito=inconclusive rules zen=['platinum-one-companion', 'platinum_one-business-chairmans'] kogito=[]
- `C088` intl_p1: zen=allow kogito=inconclusive rules zen=['platinum-one-companion', 'platinum_one-economy-chairmans'] kogito=[]
- `C090` intl_bronze_business: zen=allow kogito=inconclusive rules zen=['bronze-business-qantas_club'] kogito=[]
- `C094` peak_intl_silver_first_comp: zen=allow kogito=deny rules zen=['silver-first-first'] kogito=['seasonal-peak-deny-silver']
- `C097` peak_diamond_default_cabin_comp: zen=inconclusive kogito=allow rules zen=[] kogito=['companion-plus-one', 'tier-gold-lounge']
