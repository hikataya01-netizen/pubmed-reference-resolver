# Security Policy

## Supported Versions

セキュリティ更新の対象バージョン:

| Version | Supported |
|:---|:---:|
| 0.1.x | :white_check_mark: |
| < 0.1 | :x: |

## Reporting a Vulnerability

脆弱性を発見した場合は、**公開 Issue では報告しないでください**。

本リポジトリの [GitHub Security Advisories](https://github.com/hikataya01-netizen/pubmed-reference-resolver/security/advisories/new)
の private vulnerability reporting 機能を使用して報告してください
(リポジトリの **Security** タブ → **Report a vulnerability**)。

報告には以下を含めてください:

- 脆弱性の概要と影響範囲
- 再現手順 (可能であれば最小再現コード)
- 想定される攻撃シナリオ
- 修正案 (あれば)

## Response

- 報告受領後、合理的な期間内に初期応答します。
- 脆弱性の妥当性を確認し、修正方針と公開時期を報告者と調整します。
- 修正後、GitHub Security Advisory として公開し、報告者をクレジットします
  (希望する場合)。

## Scope and Data Handling

本プロジェクトは学術論文の参照文献を PubMed で検証する査読支援ツールです。
以下の点に特に留意してください:

- 本ツールは査読対象論文・医療関連データを処理する可能性があります。
- 脆弱性報告に患者識別情報・未公開の査読データを **含めないでください**。
  再現に必要な場合は、仮名化・匿名化したサンプルを使用してください。
- API キー (NCBI / Claude 等) の取り扱いについては
  [CONTRIBUTING.md](CONTRIBUTING.md) のセキュリティ節を参照してください。

## Related

- [CONTRIBUTING.md](CONTRIBUTING.md) — 開発フローと機密情報の取り扱い
- 機密 commit の自動防御: pre-commit gitleaks hook + CI gitleaks job
  (Day29 で導入)
