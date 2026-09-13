/* 出力① 基本レポート (references_audit_report.docx) を docx-js で生成する。
 *
 *   node build_docx.js <report_data.json> <output.docx>
 *
 * docx スキルの gotchas に準拠:
 *   - table は columnWidths と 各 cell の width を DXA で二重指定
 *   - ShadingType.CLEAR のみ使用 (SOLID は黒塗りになる)
 *   - "\n" を使わず Paragraph を分割
 *   - PageBreak は Paragraph の中に置く
 */
const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, AlignmentType, HeadingLevel, ShadingType, BorderStyle, PageBreak,
} = require('docx');

const [, , dataPath, outPath] = process.argv;
const D = JSON.parse(fs.readFileSync(dataPath, 'utf8'));

const FONT = 'Yu Mincho';
const CW = 9026;                 // A4 (11906) - 左右余白 1440*2
const HEAD = 'D9E2F3';
const GRAY = 'F2F2F2';
const ACCENT = '1A3A5C';

const T = (text, o = {}) => new TextRun({
  text: String(text == null ? '' : text),
  font: FONT,
  size: o.size || 20,
  bold: !!o.bold,
  color: o.color || '000000',
});

const P = (text, o = {}) => new Paragraph({
  alignment: o.align,
  spacing: { before: o.before == null ? 60 : o.before, after: o.after == null ? 60 : o.after },
  children: [T(text, o)],
});

const H1 = (t) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 320, after: 160 },
  children: [T(t, { size: 26, bold: true, color: ACCENT })],
});

const H2 = (t) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  spacing: { before: 220, after: 110 },
  children: [T(t, { size: 22, bold: true, color: ACCENT })],
});

const cell = (text, width, o = {}) => new TableCell({
  width: { size: width, type: WidthType.DXA },
  shading: o.fill ? { type: ShadingType.CLEAR, fill: o.fill, color: 'auto' } : undefined,
  margins: { top: 60, bottom: 60, left: 90, right: 90 },
  children: String(text == null ? '' : text).split('\u000b').map((line) => new Paragraph({
    alignment: o.align,
    spacing: { before: 20, after: 20 },
    children: [T(line, { bold: o.bold, size: o.size || 18, color: o.color })],
  })),
});

function table(widths, header, rows, opts = {}) {
  const trs = [];
  if (header) {
    trs.push(new TableRow({
      tableHeader: true,
      children: header.map((h, i) => cell(h, widths[i], {
        fill: HEAD, bold: true, size: opts.hsize || 18, align: AlignmentType.CENTER,
      })),
    }));
  }
  rows.forEach((r, ri) => trs.push(new TableRow({
    children: r.map((c, i) => cell(c, widths[i], Object.assign(
      { fill: ri % 2 ? GRAY : undefined, size: opts.size || 18,
        align: opts.align && opts.align[i] },
      (opts.cellOpts && opts.cellOpts(ri, i)) || {},
    ))),
  })));
  return new Table({
    columnWidths: widths,
    width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
    rows: trs,
  });
}

const SP = (n = 1) => Array.from({ length: n }, () => P('', { before: 0, after: 0 }));
const trunc = (s, n) => (s && String(s).length > n ? String(s).slice(0, n - 1) + '…' : String(s == null ? '' : s));

const k = [];
const S = D.summary;

/* ===================== 表紙 ===================== */
k.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { before: 800, after: 120 },
  children: [T('参考文献 監査レポート', { size: 40, bold: true, color: ACCENT })],
}));
k.push(P('PubMed 逆引きによる References セクション検証',
  { align: AlignmentType.CENTER, size: 22, color: '444444' }));
k.push(...SP(2));
k.push(table([2600, 6426], null, [
  ['入力ファイル', D.meta.source || '—'],
  ['MD5', D.meta.md5 || '—'],
  ['参照総数', `${S.total} 件`],
  ['主題', D.meta.subject || '—'],
  ['監査実施日', D.meta.date || '—'],
  ['パイプライン', D.meta.pipeline || '—'],
], { cellOpts: (r, i) => (i === 0 ? { bold: true, fill: HEAD } : {}) }));
k.push(...SP(1));
k.push(P('本レポートは、参照文献の各項目を PubMed へ逆引き照合し、実在性・書誌正確性・重複・'
  + '撤回状況を検証し、原著性・エビデンス水準・最新性・収載状況等を評価した結果である。'
  + '第 6 章には、監査ツール自身の内部点検記録を開示している。',
  { size: 19, color: '333333' }));

/* ===================== §1 ダッシュボード ===================== */
k.push(H1('1. ダッシュボード'));
k.push(P(`${S.total} 件の参考文献に対する PubMed 逆引き検証の集計結果を以下に示す。`));

const AS = D.assessment_summary || {};
const nRetr = (AS.retracted || 0) + (AS.concern || 0);
k.push(H2('1.1 解決状況サマリ'));
k.push(table([2600, 1400, 5026], ['項目', '件数', '内訳・備考'], [
  ['総参照数', `${S.total}`, '入力 References セクションの全件'],
  ['PubMed 解決', `${S.resolved}`, D.paths.filter((p) => p.path && p.path.startsWith('L'))
    .map((p) => `${p.path}: ${p.count}`).join(' / ') || '—'],
  ['PubMed 対象外', `${S.non_pubmed}`, D.non_pubmed.length
    ? `参照 ${D.non_pubmed.map((x) => `[${x.ref_no}]`).join(' ')}` : '—'],
  ['未解決', `${S.unresolved}`, D.unresolved.length
    ? `参照 ${D.unresolved.map((x) => `[${x.ref_no}]`).join(' ')}` : '全件解決済み'],
  ['撤回・懸念表明', `${nRetr}`, (D.retractions || []).length
    ? `参照 ${D.retractions.map((x) => `[${x.ref_no}]`).join(' ')} — 第 5 章参照`
    : '検出なし'],
], {
  align: [null, AlignmentType.CENTER, null],
  cellOpts: (r) => (r === 4 && nRetr > 0 ? { color: 'B00020', bold: true } : {}),
}));

k.push(H2('1.2 整合性チェックサマリ'));
k.push(table([2600, 1400, 5026], ['重要度', '件数', '意味'], [
  ['MAJOR (重大)', `${S.severity.MAJOR}`, '別論文の可能性・重複引用・未解決。必ず確認を要する'],
  ['MODERATE (要検討)', `${S.severity.MODERATE}`, '著者・編集者への確認を推奨'],
  ['MINOR (軽微)', `${S.severity.MINOR}`, '表記ゆれ等'],
  ['INFO (情報)', `${S.severity.INFO}`, '品質改善提案 (PMID/DOI 補完など)'],
], {
  align: [null, AlignmentType.CENTER, null],
  cellOpts: (r) => (r === 0 && S.severity.MAJOR > 0 ? { color: 'B00020', bold: true } : {}),
}));

k.push(H2('1.3 査読観点の総評'));
(D.meta.verdict || []).forEach((line) => k.push(P('・ ' + line, { size: 19 })));

k.push(new Paragraph({ children: [new PageBreak()] }));

/* ===================== §2 解決経路 ===================== */
k.push(H1('2. 解決経路の内訳（透明性トレース）'));
k.push(P('各参照がどの検索経路で PubMed と照合されたかを示す。上位の経路ほど確実性が高い。'));
k.push(table([1600, 1200, 6226], ['経路', '件数', '説明'],
  D.paths.map((p) => [p.path || '—', `${p.count}`, p.label]),
  { align: [AlignmentType.CENTER, AlignmentType.CENTER, null] }));

/* ===================== §3 要確認項目 ===================== */
k.push(H1('3. 要確認項目'));
const bySev = { MAJOR: [], MODERATE: [], MINOR: [], INFO: [] };
(D.issues || []).forEach((i) => bySev[i.severity].push(i));

if ((D.issues || []).length === 0) {
  k.push(P('整合性チェックで検出された問題はない。'));
}
['MAJOR', 'MODERATE', 'MINOR', 'INFO'].forEach((sev, idx) => {
  const list = bySev[sev];
  if (!list.length) return;
  k.push(H2(`3.${idx + 1} ${sev}（${list.length} 件）`));
  k.push(table([800, 2000, 3113, 3113], ['Ref#', 'カテゴリ', '内容', '引用元 / PubMed'],
    list.map((i) => [
      `[${i.ref_no}]`, i.category, trunc(i.detail, 140),
      (i.claimed ? '引用元: ' + trunc(i.claimed, 90) : '')
      + (i.claimed && i.found ? '\u000b' : '')
      + (i.found ? 'PubMed: ' + trunc(i.found, 90) : ''),
    ]),
    {
      align: [AlignmentType.CENTER, null, null, null],
      cellOpts: () => (sev === 'MAJOR' ? { color: 'B00020' } : {}),
    }));
});

k.push(new Paragraph({ children: [new PageBreak()] }));

/* ===================== §4 各文献の詳細 ===================== */
k.push(H1('4. 各文献の詳細（全件）'));
k.push(P('記号: ✓ = PubMed 解決済み、⊘ = PubMed 非対象、✗ = 未解決。'));
k.push(table([620, 520, 1000, 1300, 3286, 1500, 800],
  ['Ref#', '状態', 'PMID', '筆頭著者', 'タイトル', '雑誌', '年'],
  D.details.map((d) => [
    `${d.ref_no}`, d.mark, d.pmid, trunc(d.author, 24),
    trunc(d.title, 110), trunc(d.journal, 30), `${d.year}`,
  ]),
  {
    size: 16,
    align: [AlignmentType.CENTER, AlignmentType.CENTER, AlignmentType.CENTER,
      null, null, null, AlignmentType.CENTER],
    cellOpts: (r) => (D.details[r].status === 'UNRESOLVED' ? { color: 'B00020' } : {}),
  }));

k.push(new Paragraph({ children: [new PageBreak()] }));

/* ===================== §5 文献評価サマリ (v2) ===================== */
k.push(H1('5. 文献評価サマリ'));

k.push(H2('5.1 撤回・懸念表明の検出'));
if ((D.retractions || []).length) {
  k.push(P('以下の参照に撤回 (Retraction) または懸念表明 (Expression of Concern) が'
    + '付されている。引用の妥当性を必ず再検討し、引用が不可避な場合は撤回済みである旨を'
    + '本文に明記する必要がある。', { size: 19, color: 'B00020', bold: true }));
  k.push(table([800, 2200, 3013, 3013], ['Ref#', '種別', 'タイトル', '通知'],
    D.retractions.map((x) => [
      `[${x.ref_no}]`, x.status, trunc(x.title, 90), trunc(x.notice, 120),
    ]),
    {
      align: [AlignmentType.CENTER, AlignmentType.CENTER, null, null],
      cellOpts: () => ({ color: 'B00020' }),
    }));
} else {
  k.push(P('撤回・懸念表明が付された参照は検出されなかった。'));
}

k.push(H2('5.2 全件評価表'));
if ((D.assessments || []).length) {
  k.push(P('各参照の原著性・エビデンス水準・最新性・収載状況等の評価を示す。'
    + '未解決・PubMed 非対象の参照は評価対象外である。', { size: 19 }));
  k.push(table([620, 1100, 1500, 1300, 1300, 1200, 1100, 906],
    ['Ref#', '撤回', '原著性', '水準', '最新性', '収載', 'Predatory', '主張支持'],
    D.assessments.map((a) => [
      `${a.ref_no}`,
      a.retraction === 'CLEAN' ? '—' : a.retraction,
      a.originality, a.evidence_level, a.recency, a.indexing,
      a.predatory_risk, a.claim_support === 'NOT_ASSESSED' ? '—' : a.claim_support,
    ]),
    {
      size: 15,
      align: [AlignmentType.CENTER, AlignmentType.CENTER, null, null,
        null, AlignmentType.CENTER, AlignmentType.CENTER, AlignmentType.CENTER],
      cellOpts: (r) => {
        const a = D.assessments[r];
        if (a.retraction === 'RETRACTED' || a.retraction === 'PARTIAL_RETRACTION') {
          return { color: 'B00020' };
        }
        if (a.predatory_risk === '要確認') return { color: '8A5A00' };
        return {};
      },
    }));
} else {
  k.push(P('評価対象 (RESOLVED) の参照がない。'));
}

k.push(H2('5.3 評価方法の注記'));
k.push(P('原著性・エビデンス水準は PubMed の PublicationType のみから決定論的に分類した'
  + '参考情報である。最新性は発行年からの経過年数 (5 年以内 = 最新 / 10 年以内 = 妥当 / '
  + '10 年超 = 古い) による。収載状況は NLM Catalog (MEDLINE) と DOAJ への照会結果で'
  + 'ある。Predatory リスクは複合シグナル (MEDLINE 非収載 かつ DOAJ 非収載 かつ 書誌'
  + '直接一致以外での解決) に基づく参考フラグであり、粗悪学術誌と断定するものではない。'
  + 'Impact Factor 等の商用雑誌指標は用いていない。主張支持性は呼び出し側 LLM が引用文脈'
  + 'と抄録を突合した読解判定であり、実施時のみ表示される。', { size: 18, color: '444444' }));

k.push(new Paragraph({ children: [new PageBreak()] }));

/* ===================== §6 特筆事項 ===================== */
k.push(H1('6. 特筆事項'));

k.push(H2('6.1 PubMed 非対象と判定した参照'));
if (D.non_pubmed.length) {
  k.push(table([800, 4500, 3726], ['Ref#', 'タイトル', '非対象と判定した理由'],
    D.non_pubmed.map((x) => [`[${x.ref_no}]`, trunc(x.title, 120), x.reason]),
    { align: [AlignmentType.CENTER, null, null] }));
} else {
  k.push(P('該当なし。'));
}

k.push(H2('6.2 未解決参照の判定根拠'));
if (D.unresolved.length) {
  k.push(table([800, 3300, 2000, 2926], ['Ref#', 'タイトル', '試行経路', '推定理由'],
    D.unresolved.map((x) => [`[${x.ref_no}]`, trunc(x.title, 90), x.tried, x.note]),
    { align: [AlignmentType.CENTER, null, AlignmentType.CENTER, null] }));
} else {
  k.push(P('未解決の参照はない。'));
}

k.push(H2('6.3 内部実装の自己点検記録'));
k.push(P('本パイプラインが自ら検出した実装上の問題と、その是正内容を開示する。'
  + '結果の信頼性に直接関わるため、隠さず記載する方針を採る。', { size: 19 }));
if ((D.self_check || []).length) {
  (D.self_check || []).forEach((n, i) => k.push(P(`(${i + 1}) ${n}`, { size: 19 })));
} else {
  k.push(P('本実行では内部実装の誤りは検出されなかった。', { size: 19 }));
}

/* ===================== §7 関連出力 ===================== */
k.push(H1('7. 関連出力ファイル'));
k.push(P('本レポート（出力①）と併せて、以下の 2 ファイルを生成している。'));
k.push(table([1000, 3400, 4626], ['#', 'ファイル名', '内容'], [
  ['①', D.files.docx, '本レポート。査読結果の通読・共有・提出用'],
  ['②', D.files.csv, '全参照の構造化一覧（UTF-8 BOM 付き CSV、機械可読・二次加工用）'],
  ['③', D.files.txt, '各参照の抄録集（78 字幅ラップ、通読・引用妥当性確認用）'],
], { align: [AlignmentType.CENTER, null, null] }));

/* ===================== 出力 ===================== */
const doc = new Document({
  styles: {
    default: {
      document: { run: { font: FONT, size: 20 } },
      heading1: { run: { font: FONT } },
      heading2: { run: { font: FONT } },
    },
  },
  sections: [{
    properties: { page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    children: k,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(outPath, buf);
  console.log(`docx written: ${outPath} (${buf.length} bytes)`);
});
