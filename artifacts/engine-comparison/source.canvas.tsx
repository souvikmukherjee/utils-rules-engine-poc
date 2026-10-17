import {
  BarChart,
  Callout,
  Card,
  CardBody,
  CardHeader,
  Divider,
  Grid,
  H1,
  H2,
  H3,
  Pill,
  Row,
  Stack,
  Stat,
  Table,
  Text,
  useHostTheme,
  useState,
} from "cursor/canvas";

const D = {"s":{"decision_agree":68,"decision_agree_pct":68.0,"lounge_exact_agree":25,"lounge_exact_agree_pct":25.0,"lounge_presence_agree":68,"lounge_presence_agree_pct":68.0,"companion_agree":60,"companion_agree_pct":60.0,"benefit_agree":47,"benefit_agree_pct":47.0,"full_parity":21,"full_parity_pct":21.0,"engine_errors":0,"decision_mismatch_count":32,"lounge_taxonomy_diff_when_decision_agrees":47,"companion_mismatch_when_decision_agrees":18},"lat":{"zen":{"n":100,"min_ms":0.522,"median_ms":0.621,"mean_ms":0.682,"p95_ms":0.908,"max_ms":1.09},"kogito":{"n":100,"min_ms":15.05,"median_ms":15.793,"mean_ms":16.24,"p95_ms":20.112,"max_ms":21.226}},"ct":{"inconclusive":{"inconclusive":18,"allow":12},"allow":{"inconclusive":15,"allow":45,"deny":3},"deny":{"deny":5,"inconclusive":1,"allow":1}},"tier":{"bronze":{"n":23,"agree":16},"silver":{"n":22,"agree":15},"gold":{"n":11,"agree":11},"platinum":{"n":10,"agree":10},"platinum_one":{"n":11,"agree":3},"diamond":{"n":11,"agree":2},"unknown":{"n":8,"agree":7},"None":{"n":4,"agree":4}},"causes":{"cabin_matrix_zen_only":7,"platinum_one_zen_only":8,"diamond_kogito_only":9,"seasonal_deny_wins_zen":2,"seasonal_silver_scope":3,"companion_flag_implies_allow_kogito":3},"mm":[{"i":"C002","l":"matrix:bronze+business","c":"cabin_matrix_zen_only","z":"allow","k":"inconclusive","zr":"bronze-business-qantas_club","kr":"\u2014"},{"i":"C003","l":"matrix:bronze+first","c":"cabin_matrix_zen_only","z":"allow","k":"inconclusive","zr":"bronze-first-first","kr":"\u2014"},{"i":"C005","l":"matrix:silver+premium_economy","c":"cabin_matrix_zen_only","z":"allow","k":"inconclusive","zr":"silver-premium_economy-qantas_club","kr":"\u2014"},{"i":"C006","l":"matrix:silver+business","c":"cabin_matrix_zen_only","z":"allow","k":"inconclusive","zr":"silver-business-business","kr":"\u2014"},{"i":"C007","l":"matrix:silver+first","c":"cabin_matrix_zen_only","z":"allow","k":"inconclusive","zr":"silver-first-first","kr":"\u2014"},{"i":"C016","l":"matrix:platinum_one+economy","c":"platinum_one_zen_only","z":"allow","k":"inconclusive","zr":"platinum-one-companion,platinum_one-economy-chairmans","kr":"\u2014"},{"i":"C017","l":"matrix:platinum_one+premium_economy","c":"platinum_one_zen_only","z":"allow","k":"inconclusive","zr":"platinum-one-companion,platinum_one-premium_economy-chairmans","kr":"\u2014"},{"i":"C018","l":"matrix:platinum_one+business","c":"platinum_one_zen_only","z":"allow","k":"inconclusive","zr":"platinum-one-companion,platinum_one-business-chairmans","kr":"\u2014"},{"i":"C019","l":"matrix:platinum_one+first","c":"platinum_one_zen_only","z":"allow","k":"inconclusive","zr":"platinum-one-companion,platinum_one-first-chairmans","kr":"\u2014"},{"i":"C020","l":"matrix:diamond+economy","c":"diamond_kogito_only","z":"inconclusive","k":"allow","zr":"\u2014","kr":"companion-plus-one,tier-gold-lounge"},{"i":"C021","l":"matrix:diamond+premium_economy","c":"diamond_kogito_only","z":"inconclusive","k":"allow","zr":"\u2014","kr":"companion-plus-one,tier-gold-lounge"},{"i":"C022","l":"matrix:diamond+business","c":"diamond_kogito_only","z":"inconclusive","k":"allow","zr":"\u2014","kr":"companion-plus-one,tier-gold-lounge"},{"i":"C023","l":"matrix:diamond+first","c":"diamond_kogito_only","z":"inconclusive","k":"allow","zr":"\u2014","kr":"companion-plus-one,tier-gold-lounge"},{"i":"C032","l":"default_cabin:diamond","c":"diamond_kogito_only","z":"inconclusive","k":"allow","zr":"\u2014","kr":"companion-plus-one,tier-gold-lounge"},{"i":"C034","l":"default_cabin:platinum_one","c":"platinum_one_zen_only","z":"allow","k":"inconclusive","zr":"platinum-one-companion,platinum_one-economy-chairmans","kr":"\u2014"},{"i":"C056","l":"peak_bronze_economy","c":"seasonal_deny_wins_zen","z":"deny","k":"inconclusive","zr":"seasonal-peak-deny-low-tier","kr":"\u2014"},{"i":"C057","l":"peak_silver_business","c":"seasonal_silver_scope","z":"allow","k":"deny","zr":"silver-business-business","kr":"seasonal-peak-deny-silver"},{"i":"C060","l":"peak_bronze_partner","c":"seasonal_deny_wins_zen","z":"deny","k":"allow","zr":"partner-elite-club,seasonal-peak-deny-low-tier","kr":"partner-elite-access"},{"i":"C065","l":"peak_diamond","c":"diamond_kogito_only","z":"inconclusive","k":"allow","zr":"\u2014","kr":"companion-plus-one,tier-gold-lounge"},{"i":"C066","l":"peak_silver_prem","c":"seasonal_silver_scope","z":"allow","k":"deny","zr":"silver-premium_economy-qantas_club","kr":"seasonal-peak-deny-silver"},{"i":"C068","l":"peak_bronze_first","c":"cabin_matrix_zen_only","z":"allow","k":"inconclusive","zr":"bronze-first-first","kr":"\u2014"},{"i":"C071","l":"comp_on_bronze","c":"companion_flag_implies_allow_kogito","z":"inconclusive","k":"allow","zr":"\u2014","kr":"companion-plus-one"},{"i":"C076","l":"comp_off_p1","c":"platinum_one_zen_only","z":"allow","k":"inconclusive","zr":"platinum-one-companion,platinum_one-economy-chairmans","kr":"\u2014"},{"i":"C078","l":"comp_off_diamond","c":"diamond_kogito_only","z":"inconclusive","k":"allow","zr":"\u2014","kr":"companion-plus-one,tier-gold-lounge"},{"i":"C079","l":"comp_on_diamond","c":"diamond_kogito_only","z":"inconclusive","k":"allow","zr":"\u2014","kr":"companion-plus-one,tier-gold-lounge"},{"i":"C080","l":"comp_on_unknown","c":"companion_flag_implies_allow_kogito","z":"inconclusive","k":"allow","zr":"\u2014","kr":"companion-plus-one"},{"i":"C082","l":"comp_on_silver_econ","c":"companion_flag_implies_allow_kogito","z":"inconclusive","k":"allow","zr":"\u2014","kr":"companion-plus-one"},{"i":"C084","l":"comp_off_p1_biz","c":"platinum_one_zen_only","z":"allow","k":"inconclusive","zr":"platinum-one-companion,platinum_one-business-chairmans","kr":"\u2014"},{"i":"C088","l":"intl_p1","c":"platinum_one_zen_only","z":"allow","k":"inconclusive","zr":"platinum-one-companion,platinum_one-economy-chairmans","kr":"\u2014"},{"i":"C090","l":"intl_bronze_business","c":"cabin_matrix_zen_only","z":"allow","k":"inconclusive","zr":"bronze-business-qantas_club","kr":"\u2014"},{"i":"C094","l":"peak_intl_silver_first_comp","c":"seasonal_silver_scope","z":"allow","k":"deny","zr":"silver-first-first","kr":"seasonal-peak-deny-silver"},{"i":"C097","l":"peak_diamond_default_cabin_comp","c":"diamond_kogito_only","z":"inconclusive","k":"allow","zr":"\u2014","kr":"companion-plus-one,tier-gold-lounge"}],"o":[{"i":"C000","l":"matrix:bronze+economy","z":"i","k":"i","a":true,"zl":"","kl":""},{"i":"C001","l":"matrix:bronze+premium_economy","z":"i","k":"i","a":true,"zl":"","kl":""},{"i":"C002","l":"matrix:bronze+business","z":"a","k":"i","a":false,"zl":"qantas_club","kl":""},{"i":"C003","l":"matrix:bronze+first","z":"a","k":"i","a":false,"zl":"first","kl":""},{"i":"C004","l":"matrix:silver+economy","z":"i","k":"i","a":true,"zl":"","kl":""},{"i":"C005","l":"matrix:silver+premium_economy","z":"a","k":"i","a":false,"zl":"qantas_club","kl":""},{"i":"C006","l":"matrix:silver+business","z":"a","k":"i","a":false,"zl":"business","kl":""},{"i":"C007","l":"matrix:silver+first","z":"a","k":"i","a":false,"zl":"first","kl":""},{"i":"C008","l":"matrix:gold+economy","z":"a","k":"a","a":true,"zl":"qantas_club","kl":"domestic"},{"i":"C009","l":"matrix:gold+premium_economy","z":"a","k":"a","a":true,"zl":"qantas_club","kl":"domestic"},{"i":"C010","l":"matrix:gold+business","z":"a","k":"a","a":true,"zl":"business","kl":"domestic"},{"i":"C011","l":"matrix:gold+first","z":"a","k":"a","a":true,"zl":"first","kl":"domestic"},{"i":"C012","l":"matrix:platinum+economy","z":"a","k":"a","a":true,"zl":"business","kl":"domestic"},{"i":"C013","l":"matrix:platinum+premium_economy","z":"a","k":"a","a":true,"zl":"business","kl":"domestic"},{"i":"C014","l":"matrix:platinum+business","z":"a","k":"a","a":true,"zl":"first","kl":"domestic"},{"i":"C015","l":"matrix:platinum+first","z":"a","k":"a","a":true,"zl":"first","kl":"domestic"},{"i":"C016","l":"matrix:platinum_one+economy","z":"a","k":"i","a":false,"zl":"chairmans","kl":""},{"i":"C017","l":"matrix:platinum_one+premium_economy","z":"a","k":"i","a":false,"zl":"chairmans","kl":""},{"i":"C018","l":"matrix:platinum_one+business","z":"a","k":"i","a":false,"zl":"chairmans","kl":""},{"i":"C019","l":"matrix:platinum_one+first","z":"a","k":"i","a":false,"zl":"chairmans","kl":""},{"i":"C020","l":"matrix:diamond+economy","z":"i","k":"a","a":false,"zl":"","kl":"domestic"},{"i":"C021","l":"matrix:diamond+premium_economy","z":"i","k":"a","a":false,"zl":"","kl":"domestic"},{"i":"C022","l":"matrix:diamond+business","z":"i","k":"a","a":false,"zl":"","kl":"domestic"},{"i":"C023","l":"matrix:diamond+first","z":"i","k":"a","a":false,"zl":"","kl":"domestic"},{"i":"C024","l":"matrix:unknown+economy","z":"i","k":"i","a":true,"zl":"","kl":""},{"i":"C025","l":"matrix:unknown+business","z":"i","k":"i","a":true,"zl":"","kl":""},{"i":"C026","l":"matrix:unknown+first","z":"i","k":"i","a":true,"zl":"","kl":""},{"i":"C027","l":"matrix:null_tier+economy","z":"i","k":"i","a":true,"zl":"","kl":""},{"i":"C028","l":"matrix:null_tier+first","z":"i","k":"i","a":true,"zl":"","kl":""},{"i":"C029","l":"default_cabin:bronze","z":"i","k":"i","a":true,"zl":"","kl":""},{"i":"C030","l":"default_cabin:gold","z":"a","k":"a","a":true,"zl":"qantas_club","kl":"domestic"},{"i":"C031","l":"default_cabin:platinum","z":"a","k":"a","a":true,"zl":"business","kl":"domestic"},{"i":"C032","l":"default_cabin:diamond","z":"i","k":"a","a":false,"zl":"","kl":"domestic"},{"i":"C033","l":"default_cabin:silver","z":"i","k":"i","a":true,"zl":"","kl":""},{"i":"C034","l":"default_cabin:platinum_one","z":"a","k":"i","a":false,"zl":"chairmans","kl":""},{"i":"C035","l":"partner:bronze+economy+elite:gold","z":"a","k":"a","a":true,"zl":"qantas_club","kl":"domestic"},{"i":"C036","l":"partner:bronze+economy+elite:platinum","z":"a","k":"a","a":true,"zl":"qantas_club","kl":"domestic"},{"i":"C037","l":"partner:bronze+economy+elite:first","z":"a","k":"a","a":true,"zl":"qantas_club","kl":"domestic"},{"i":"C038","l":"partner:bronze+first+elite:gold","z":"a","k":"a","a":true,"zl":"first,qantas_club","kl":"domestic"},{"i":"C039","l":"partner:silver+economy+elite:gold","z":"a","k":"a","a":true,"zl":"qantas_club","kl":"domestic"},{"i":"C040","l":"partner:silver+premium_economy+elite:pla","z":"a","k":"a","a":true,"zl":"qantas_club","kl":"domestic"},{"i":"C041","l":"partner:silver+business+elite:first","z":"a","k":"a","a":true,"zl":"business,qantas_club","kl":"domestic"},{"i":"C042","l":"partner:gold+economy+elite:gold","z":"a","k":"a","a":true,"zl":"qantas_club","kl":"domestic"},{"i":"C043","l":"partner:platinum+economy+elite:first","z":"a","k":"a","a":true,"zl":"business,qantas_club","kl":"domestic"},{"i":"C044","l":"partner:unknown+economy+elite:gold","z":"a","k":"a","a":true,"zl":"qantas_club","kl":"domestic"},{"i":"C045","l":"partner:bronze+economy+elite:silver","z":"i","k":"i","a":true,"zl":"","kl":""},{"i":"C046","l":"partner:bronze+economy+elite:unknown","z":"i","k":"i","a":true,"zl":"","kl":""},{"i":"C047","l":"partner:None+economy+elite:gold","z":"a","k":"a","a":true,"zl":"qantas_club","kl":"domestic"},{"i":"C048","l":"partner:bronze+None+elite:platinum","z":"a","k":"a","a":true,"zl":"qantas_club","kl":"domestic"},{"i":"C049","l":"partner:silver+economy+elite:gold","z":"a","k":"a","a":true,"zl":"qantas_club","kl":"domestic"},{"i":"C050","l":"partner:diamond+economy+elite:gold","z":"a","k":"a","a":true,"zl":"qantas_club","kl":"domestic"},{"i":"C051","l":"partner:platinum_one+economy+elite:gold","z":"a","k":"a","a":true,"zl":"chairmans,qantas_club","kl":"domestic"},{"i":"C052","l":"partner:bronze+business+elite:gold","z":"a","k":"a","a":true,"zl":"qantas_club","kl":"domestic"},{"i":"C053","l":"partner:silver+first+elite:platinum","z":"a","k":"a","a":true,"zl":"first,qantas_club","kl":"domestic"},{"i":"C054","l":"partner:unknown+first+elite:first","z":"a","k":"a","a":true,"zl":"qantas_club","kl":"domestic"},{"i":"C055","l":"peak_silver_economy","z":"d","k":"d","a":true,"zl":"","kl":""},{"i":"C056","l":"peak_bronze_economy","z":"d","k":"i","a":false,"zl":"","kl":""},{"i":"C057","l":"peak_silver_business","z":"a","k":"d","a":false,"zl":"business","kl":""},{"i":"C058","l":"peak_gold_economy","z":"a","k":"a","a":true,"zl":"qantas_club","kl":"domestic"},{"i":"C059","l":"peak_silver_partner","z":"d","k":"d","a":true,"zl":"qantas_club","kl":""},{"i":"C060","l":"peak_bronze_partner","z":"d","k":"a","a":false,"zl":"qantas_club","kl":"domestic"},{"i":"C061","l":"prepeak_silver","z":"i","k":"i","a":true,"zl":"","kl":""},{"i":"C062","l":"postpeak_silver","z":"i","k":"i","a":true,"zl":"","kl":""},{"i":"C063","l":"prepeak_bronze","z":"i","k":"i","a":true,"zl":"","kl":""},{"i":"C064","l":"peak_platinum","z":"a","k":"a","a":true,"zl":"business","kl":"domestic"},{"i":"C065","l":"peak_diamond","z":"i","k":"a","a":false,"zl":"","kl":"domestic"},{"i":"C066","l":"peak_silver_prem","z":"a","k":"d","a":false,"zl":"qantas_club","kl":""},{"i":"C067","l":"peak_silver_default_cabin","z":"d","k":"d","a":true,"zl":"","kl":""},{"i":"C068","l":"peak_bronze_first","z":"a","k":"i","a":false,"zl":"first","kl":""},{"i":"C069","l":"peak_unknown","z":"i","k":"i","a":true,"zl":"","kl":""},{"i":"C070","l":"comp_off_bronze","z":"i","k":"i","a":true,"zl":"","kl":""},{"i":"C071","l":"comp_on_bronze","z":"i","k":"a","a":false,"zl":"","kl":""},{"i":"C072","l":"comp_on_silver","z":"a","k":"a","a":true,"zl":"business","kl":""},{"i":"C073","l":"comp_on_gold","z":"a","k":"a","a":true,"zl":"qantas_club","kl":"domestic"},{"i":"C074","l":"comp_off_platinum","z":"a","k":"a","a":true,"zl":"business","kl":"domestic"},{"i":"C075","l":"comp_on_platinum","z":"a","k":"a","a":true,"zl":"business","kl":"domestic"},{"i":"C076","l":"comp_off_p1","z":"a","k":"i","a":false,"zl":"chairmans","kl":""},{"i":"C077","l":"comp_on_p1","z":"a","k":"a","a":true,"zl":"chairmans","kl":""},{"i":"C078","l":"comp_off_diamond","z":"i","k":"a","a":false,"zl":"","kl":"domestic"},{"i":"C079","l":"comp_on_diamond","z":"i","k":"a","a":false,"zl":"","kl":"domestic"},{"i":"C080","l":"comp_on_unknown","z":"i","k":"a","a":false,"zl":"","kl":""},{"i":"C081","l":"comp_on_bronze_first","z":"a","k":"a","a":true,"zl":"first","kl":""},{"i":"C082","l":"comp_on_silver_econ","z":"i","k":"a","a":false,"zl":"","kl":""},{"i":"C083","l":"comp_on_gold_first","z":"a","k":"a","a":true,"zl":"first","kl":"domestic"},{"i":"C084","l":"comp_off_p1_biz","z":"a","k":"i","a":false,"zl":"chairmans","kl":""},{"i":"C085","l":"intl_gold_partner","z":"a","k":"a","a":true,"zl":"qantas_club","kl":"domestic"},{"i":"C086","l":"intl_bronze_partner_comp","z":"a","k":"a","a":true,"zl":"qantas_club","kl":"domestic"},{"i":"C087","l":"peak_intl_silver_partner","z":"d","k":"d","a":true,"zl":"qantas_club","kl":""},{"i":"C088","l":"intl_p1","z":"a","k":"i","a":false,"zl":"chairmans","kl":""},{"i":"C089","l":"intl_diamond_all_signals","z":"a","k":"a","a":true,"zl":"qantas_club","kl":"domestic"},{"i":"C090","l":"intl_bronze_business","z":"a","k":"i","a":false,"zl":"qantas_club","kl":""},{"i":"C091","l":"sparse_partner_comp","z":"a","k":"a","a":true,"zl":"qantas_club","kl":"domestic"},{"i":"C092","l":"empty_almost","z":"i","k":"i","a":true,"zl":"","kl":""},{"i":"C093","l":"intl_gold_low_partner","z":"a","k":"a","a":true,"zl":"qantas_club","kl":"domestic"},{"i":"C094","l":"peak_intl_silver_first_comp","z":"a","k":"d","a":false,"zl":"first","kl":""},{"i":"C095","l":"postpeak_plat_partner","z":"a","k":"a","a":true,"zl":"business,qantas_club","kl":"domestic"},{"i":"C096","l":"prepeak_bronze_partner","z":"a","k":"a","a":true,"zl":"qantas_club","kl":"domestic"},{"i":"C097","l":"peak_diamond_default_cabin_comp","z":"i","k":"a","a":false,"zl":"","kl":"domestic"},{"i":"C098","l":"p1_full_stack","z":"a","k":"a","a":true,"zl":"chairmans,qantas_club","kl":"domestic"},{"i":"C099","l":"peak_silver_baseline_repeat","z":"d","k":"d","a":true,"zl":"","kl":""}]} as const;

type Filter = "all" | "agree" | "mismatch";

const CAUSE: Record<string, string> = {
  diamond_kogito_only: "Diamond only in Kogito",
  platinum_one_zen_only: "Platinum One only in Zen",
  cabin_matrix_zen_only: "Cabin matrix only in Zen",
  seasonal_silver_scope: "Seasonal silver wider in Kogito",
  seasonal_deny_wins_zen: "Seasonal deny-wins in Zen",
  companion_flag_implies_allow_kogito: "Companion flag → allow in Kogito",
};

const DEC: Record<string, string> = { a: "allow", d: "deny", i: "inconclusive" };

function pct(n: number): string {
  return `${n.toFixed(1)}%`;
}

export default function EngineComparisonCanvas() {
  useHostTheme();
  const [filter, setFilter] = useState<Filter>("all");
  const s = D.s;
  const rows = D.o.filter((c) => {
    if (filter === "agree") return c.a;
    if (filter === "mismatch") return !c.a;
    return true;
  });

  const ct = D.ct as Record<string, Record<string, number>>;
  const byTier = D.tier as Record<string, { n: number; agree: number }>;
  const tierCats = Object.keys(byTier);
  const tierAgree = tierCats.map((t) => {
    const x = byTier[t];
    return x.n ? Math.round((100 * x.agree) / x.n) : 0;
  });
  const causes = Object.entries(D.causes as Record<string, number>).sort((a, b) => b[1] - a[1]);

  return (
    <Stack gap={24} style={{ maxWidth: 1100 }}>
      <Stack gap={8}>
        <H1>Zen vs Kogito — 100 complex cases</H1>
        <Text tone="secondary">
          Objective parity: Zen JDM lounge-access 2.0.0 vs Kogito LoungeAccess.dmn. Same facts,
          both engines, 0 errors. Primary metric: decision parity.
        </Text>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat value={`${s.decision_agree}/100`} label="Decision agreement" tone="warning" />
        <Stat value={pct(s.decision_agree_pct)} label="Decision agree rate" tone="warning" />
        <Stat value={pct(s.full_parity_pct)} label="Full parity" tone="danger" />
        <Stat value={String(s.engine_errors)} label="Engine errors" tone="success" />
      </Grid>

      <Grid columns={4} gap={12}>
        <Stat value={pct(s.lounge_exact_agree_pct)} label="Exact lounge match" />
        <Stat value={pct(s.lounge_presence_agree_pct)} label="Lounge presence match" />
        <Stat value={pct(s.companion_agree_pct)} label="Companion agreement" />
        <Stat value={pct(s.benefit_agree_pct)} label="Benefit agreement" />
      </Grid>

      <Callout tone="warning" title="Not semantically equivalent">
        Zen: tier×cabin matrix, partner overlay, platinum_one companion, seasonal deny for
        bronze/silver economy. Kogito: gold/platinum/diamond or partner elite → allow
        (lounge always &quot;domestic&quot;); seasonal deny for all silver in 2099; CompanionEligible
        alone can yield allow via companion grant.
      </Callout>

      <H2>Decision contingency (Zen rows / Kogito cols)</H2>
      <Table
        headers={["Zen / Kogito", "allow", "deny", "inconclusive", "Total"]}
        columnAlign={["left", "right", "right", "right", "right"]}
        rows={(["allow", "deny", "inconclusive"] as const).map((z) => {
          const r = ct[z] || {};
          const a = r.allow || 0;
          const d = r.deny || 0;
          const i = r.inconclusive || 0;
          return [z, String(a), String(d), String(i), String(a + d + i)];
        })}
      />

      <Grid columns={2} gap={16}>
        <Stack gap={8}>
          <H2>Agreement by tier</H2>
          <Text tone="secondary" size="small">Decision agree % · this run · 100 cases</Text>
          <BarChart
            categories={tierCats.map((t) => (t === "None" ? "null" : t))}
            series={[{ name: "Agree %", data: tierAgree, tone: "info" }]}
            yMax={100}
            height={220}
          />
        </Stack>
        <Stack gap={8}>
          <H2>Mismatch causes (32)</H2>
          <BarChart
            horizontal
            categories={causes.map(([k]) => CAUSE[k] || k)}
            series={[{ name: "Count", data: causes.map(([, v]) => v), tone: "danger" }]}
            height={260}
          />
        </Stack>
      </Grid>

      <H2>Latency</H2>
      <Text tone="secondary" size="small">
        After warmup · Zen in-process · Kogito HTTP :8081
      </Text>
      <Grid columns={2} gap={12}>
        <Card>
          <CardHeader>Zen</CardHeader>
          <CardBody>
            <Text>
              median {D.lat.zen.median_ms} ms · p95 {D.lat.zen.p95_ms} ms · max {D.lat.zen.max_ms} ms
            </Text>
          </CardBody>
        </Card>
        <Card>
          <CardHeader>Kogito</CardHeader>
          <CardBody>
            <Text>
              median {D.lat.kogito.median_ms} ms · p95 {D.lat.kogito.p95_ms} ms · max {D.lat.kogito.max_ms}{" "}
              ms
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <H2>Divergence themes</H2>
      <Grid columns={2} gap={12}>
        <Card>
          <CardHeader trailing={<Pill>8</Pill>}>Platinum One (Zen only)</CardHeader>
          <CardBody>
            <Text size="small">Zen → Chairman&apos;s + companion. Kogito unknown tier → inconclusive.</Text>
          </CardBody>
        </Card>
        <Card>
          <CardHeader trailing={<Pill>9</Pill>}>Diamond (Kogito only)</CardHeader>
          <CardBody>
            <Text size="small">Kogito maps diamond with gold/platinum. Zen matrix has no diamond rows.</Text>
          </CardBody>
        </Card>
        <Card>
          <CardHeader trailing={<Pill>7</Pill>}>Cabin upgrades (Zen only)</CardHeader>
          <CardBody>
            <Text size="small">Bronze/silver cabin unlocks in Zen. Kogito ignores cabin entirely.</Text>
          </CardBody>
        </Card>
        <Card>
          <CardHeader trailing={<Pill>8</Pill>}>Seasonal + companion</CardHeader>
          <CardBody>
            <Text size="small">
              Kogito denies all silver in 2099; Zen only economy. Companion flag alone can allow in Kogito.
            </Text>
          </CardBody>
        </Card>
      </Grid>

      <Divider />

      <H2>All 100 outcomes</H2>
      <Row gap={8} wrap>
        <Pill active={filter === "all"} onClick={() => setFilter("all")}>
          All ({D.o.length})
        </Pill>
        <Pill active={filter === "agree"} onClick={() => setFilter("agree")}>
          Agree ({D.o.filter((c) => c.a).length})
        </Pill>
        <Pill active={filter === "mismatch"} onClick={() => setFilter("mismatch")}>
          Mismatch ({D.o.filter((c) => !c.a).length})
        </Pill>
      </Row>

      <Table
        stickyHeader
        striped
        headers={["Case", "Label", "Zen", "Kogito", "Zen lounge", "Kogito lounge"]}
        rowTone={rows.map((c) => (c.a ? "success" : "danger"))}
        rows={rows.map((c) => [
          c.i,
          c.l,
          DEC[c.z] || c.z,
          DEC[c.k] || c.k,
          c.zl || "—",
          c.kl || "—",
        ])}
        style={{ maxHeight: 480 }}
      />

      <H2>32 decision mismatches</H2>
      <Table
        stickyHeader
        striped
        headers={["Case", "Cause", "Zen", "Kogito", "Zen rules", "Kogito rules"]}
        rowTone={D.mm.map(() => "danger" as const)}
        rows={D.mm.map((m) => [
          `${m.i} ${m.l}`,
          CAUSE[m.c] || m.c,
          m.z,
          m.k,
          m.zr,
          m.kr,
        ])}
        style={{ maxHeight: 360 }}
      />

      <H3>Method</H3>
      <Text size="small" tone="secondary">
        scripts/compare_engines_100.py · 35 matrix · 20 partner · 15 seasonal · 15 companion · 15
        multi-signal · artifacts/engine-comparison/zen_vs_kogito_100.json
      </Text>
    </Stack>
  );
}
