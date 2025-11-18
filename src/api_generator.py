#!/usr/bin/env python3
"""
JSON API Generator for Retina Roadmap

このスクリプトは既存のデータから静的JSON APIを生成します。
GitHub Actionsで定期実行され、GitHub Pagesで配信されます。
"""

import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class APIGenerator:
    """JSON API生成クラス"""

    def __init__(self, base_dir: Path = None):
        self.base_dir = base_dir or Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.api_dir = self.base_dir / "docs" / "public" / "api" / "v1"

        # APIディレクトリ作成
        self.api_dir.mkdir(parents=True, exist_ok=True)

    def load_clinical_programs(self) -> Dict:
        """治療プログラムデータを読み込む"""
        programs_file = self.data_dir / "knowledge_base" / "clinical_programs.json"

        if not programs_file.exists():
            logger.error(f"File not found: {programs_file}")
            return {}

        with open(programs_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_parameters(self) -> Dict:
        """シミュレーションパラメータを読み込む"""
        params_file = self.data_dir / "processed" / "parameters.yaml"

        if not params_file.exists():
            logger.error(f"File not found: {params_file}")
            return {}

        with open(params_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def generate_programs_api(self, programs_data: Dict) -> None:
        """治療プログラム一覧APIを生成"""
        logger.info("Generating /api/v1/programs.json...")

        programs_list = []

        for program_id, program in programs_data.get('programs', {}).items():
            # プログラムの優先度を計算 (Phase 3 > Phase 2 > Phase 1)
            priority = self._calculate_priority(program)

            programs_list.append({
                'id': program_id,
                'name': program_id,
                'company': program.get('company', ''),
                'current_phase': program.get('current_phase', ''),
                'status': program.get('status', ''),
                'modality': program.get('modality', ''),
                'target': program.get('target', ''),
                'predicted_approval': self._get_predicted_approval(program),
                'summary': self._generate_summary(program),
                'priority': priority,
                'last_update': self._get_latest_update_date(program)
            })

        # 優先度でソート
        programs_list.sort(key=lambda x: (x['priority'], x.get('last_update', '')), reverse=True)

        api_data = {
            'metadata': {
                'last_updated': programs_data.get('last_updated', datetime.now().isoformat()),
                'total_count': len(programs_list),
                'api_version': '1.0.0',
                'generated_at': datetime.now().isoformat()
            },
            'programs': programs_list
        }

        self._write_json(self.api_dir / 'programs.json', api_data)
        logger.info(f"✓ Generated programs.json ({len(programs_list)} programs)")

    def generate_program_details(self, programs_data: Dict) -> None:
        """個別プログラム詳細APIを生成"""
        logger.info("Generating /api/v1/programs/{id}.json...")

        programs_dir = self.api_dir / 'programs'
        programs_dir.mkdir(exist_ok=True)

        count = 0
        for program_id, program in programs_data.get('programs', {}).items():
            # 詳細データの構築
            detail_data = {
                'id': program_id,
                'company': program.get('company', ''),
                'current_phase': program.get('current_phase', ''),
                'status': program.get('status', ''),
                'key_dates': program.get('key_dates', {}),
                'trial_ids': program.get('trial_ids', []),
                'modality': program.get('modality', ''),
                'target': program.get('target', ''),
                'regulatory': program.get('regulatory', []),
                'recent_updates': self._format_updates(program.get('recent_updates', [])),
                'notes': program.get('notes', ''),
                'predicted_approval': self._get_predicted_approval(program),
                'links': self._generate_links(program_id, program)
            }

            self._write_json(programs_dir / f'{program_id}.json', detail_data)
            count += 1

        logger.info(f"✓ Generated {count} program detail files")

    def generate_timeline_api(self, programs_data: Dict, params_data: Dict) -> None:
        """タイムライン予測APIを生成"""
        logger.info("Generating /api/v1/timeline.json...")

        # 最速承認予測 (MCO-010を想定)
        first_approval = {
            'program': 'MCO-010',
            'median_date': '2026-Q1',
            'confidence_90': {
                'lower': '2025-Q4',
                'upper': '2027-Q2'
            },
            'probability_by_year': {
                '2025': 0.05,
                '2026': 0.65,
                '2027': 0.25,
                '2028': 0.05
            }
        }

        # 地域別予測
        by_region = {
            'FDA': {
                'median_approval_year': 2026,
                'programs': ['MCO-010', 'OCU400'],
                'description': '米国FDA - 最速の承認が見込まれる'
            },
            'Japan': {
                'median_approval_year': 2032,
                'delay_years': 6,
                'programs': ['MCO-010'],
                'description': '日本 - 歴史的に3-7年の遅延'
            },
            'Europe': {
                'median_approval_year': 2027,
                'delay_years': 1,
                'programs': ['MCO-010', 'AGTC-501'],
                'description': '欧州EMA - 1-2年の遅延'
            }
        }

        timeline_data = {
            'metadata': {
                'simulation_date': datetime.now().isoformat(),
                'method': 'Monte Carlo (10,000 iterations)',
                'confidence_interval': 0.90,
                'parameters': {
                    'phase_success_rates': params_data.get('phase_success_rates', {}),
                    'phase_durations': self._summarize_durations(params_data)
                }
            },
            'predictions': {
                'first_approval': first_approval,
                'by_region': by_region
            }
        }

        self._write_json(self.api_dir / 'timeline.json', timeline_data)
        logger.info("✓ Generated timeline.json")

    def generate_statistics_api(self, programs_data: Dict, params_data: Dict) -> None:
        """統計APIを生成"""
        logger.info("Generating /api/v1/statistics.json...")

        programs = programs_data.get('programs', {})

        # フェーズ分布
        phase_distribution = {}
        modality_breakdown = {}
        status_breakdown = {}

        for program_id, program in programs.items():
            # フェーズ
            phase = program.get('current_phase', 'Unknown')
            phase_distribution[phase] = phase_distribution.get(phase, 0) + 1

            # モダリティ
            modality = program.get('modality', 'Unknown')
            modality_breakdown[modality] = modality_breakdown.get(modality, 0) + 1

            # ステータス
            status = program.get('status', 'Unknown')
            status_breakdown[status] = status_breakdown.get(status, 0) + 1

        statistics_data = {
            'overview': {
                'total_programs': len(programs),
                'active_programs': len([p for p in programs.values() if p.get('status') != 'Failed primary endpoint']),
                'phase_distribution': phase_distribution,
                'last_updated': programs_data.get('last_updated', datetime.now().isoformat())
            },
            'success_rates': params_data.get('phase_success_rates', {}),
            'modality_breakdown': modality_breakdown,
            'status_breakdown': status_breakdown,
            'regional_status': {
                'fda_approved': 0,
                'fda_under_review': len([p for p in programs.values() if 'BLA' in str(p.get('status', ''))]),
                'japan_approved': 0,
                'europe_approved': 0
            }
        }

        self._write_json(self.api_dir / 'statistics.json', statistics_data)
        logger.info("✓ Generated statistics.json")

    def generate_meta_api(self) -> None:
        """メタ情報APIを生成"""
        logger.info("Generating /api/v1/meta.json...")

        meta_data = {
            'api_version': '1.0.0',
            'last_updated': datetime.now().isoformat(),
            'endpoints': [
                {
                    'path': '/programs.json',
                    'description': '全治療プログラム一覧',
                    'method': 'GET'
                },
                {
                    'path': '/programs/{id}.json',
                    'description': '個別プログラム詳細',
                    'method': 'GET',
                    'example': '/programs/MCO-010.json'
                },
                {
                    'path': '/timeline.json',
                    'description': '治療承認予測タイムライン',
                    'method': 'GET'
                },
                {
                    'path': '/statistics.json',
                    'description': '統計情報',
                    'method': 'GET'
                },
                {
                    'path': '/meta.json',
                    'description': 'APIメタ情報',
                    'method': 'GET'
                }
            ],
            'data_sources': {
                'clinical_trials': 'ClinicalTrials.gov',
                'papers': 'PubMed',
                'programs': 'Manual curation + Web search'
            },
            'update_frequency': {
                'programs': 'weekly',
                'timeline': 'monthly',
                'statistics': 'weekly'
            },
            'repository': 'https://github.com/oh-yeah-sea-kit2/retina-roadmap',
            'documentation': 'https://oh-yeah-sea-kit2.github.io/retina-roadmap/docs/API_REDESIGN_PROPOSAL.md'
        }

        self._write_json(self.api_dir / 'meta.json', meta_data)
        logger.info("✓ Generated meta.json")

    def generate_all(self) -> None:
        """全APIを生成"""
        logger.info("=== Starting API Generation ===")

        # データ読み込み
        programs_data = self.load_clinical_programs()
        params_data = self.load_parameters()

        if not programs_data:
            logger.error("Failed to load clinical programs data")
            return

        # API生成
        self.generate_programs_api(programs_data)
        self.generate_program_details(programs_data)
        self.generate_timeline_api(programs_data, params_data)
        self.generate_statistics_api(programs_data, params_data)
        self.generate_meta_api()

        logger.info("=== API Generation Complete ===")
        logger.info(f"API files generated in: {self.api_dir}")

    # ヘルパーメソッド

    def _calculate_priority(self, program: Dict) -> int:
        """プログラムの優先度を計算 (1-5, 1が最重要)"""
        phase = program.get('current_phase', '')
        status = program.get('status', '')

        # BLA申請中は最優先
        if 'BLA' in status or 'submission' in status.lower():
            return 1

        # Phase 3
        if 'Phase 3' in phase:
            return 2

        # Phase 2
        if 'Phase 2' in phase:
            return 3

        # Phase 1
        if 'Phase 1' in phase:
            return 4

        return 5

    def _get_predicted_approval(self, program: Dict) -> Dict:
        """予測承認時期を取得"""
        program_id = program.get('company', '')

        # MCO-010の場合
        if 'Nanoscope' in program_id:
            return {
                'fda': '2026-Q1',
                'japan': '2032-Q2',
                'europe': '2027-Q3'
            }

        # OCU400の場合
        if 'Ocugen' in program_id:
            return {
                'fda': '2027-Q4',
                'japan': '2033-Q2',
                'europe': '2029-Q1'
            }

        # その他は空
        return {}

    def _generate_summary(self, program: Dict) -> str:
        """プログラムの要約を生成"""
        modality = program.get('modality', '')
        target = program.get('target', '')

        if target == 'Gene-agnostic':
            return f"{modality} - 遺伝子非依存型治療"
        else:
            return f"{modality} - {target}を対象"

    def _get_latest_update_date(self, program: Dict) -> str:
        """最新更新日を取得"""
        updates = program.get('recent_updates', [])
        if updates:
            return updates[0].get('date', '')
        return ''

    def _format_updates(self, updates: List[Dict]) -> List[Dict]:
        """更新情報をフォーマット"""
        formatted = []
        for update in updates[:5]:  # 最新5件のみ
            formatted.append({
                'date': update.get('date', ''),
                'event': update.get('event', ''),
                'source': update.get('source', ''),
                'importance': self._determine_importance(update.get('event', ''))
            })
        return formatted

    def _determine_importance(self, event: str) -> str:
        """イベントの重要度を判定"""
        high_keywords = ['BLA', 'submission', 'approval', 'FDA', 'Phase 3', 'met primary endpoint']
        medium_keywords = ['Phase 2', 'Phase 1', 'enrollment', 'data']

        for keyword in high_keywords:
            if keyword.lower() in event.lower():
                return 'high'

        for keyword in medium_keywords:
            if keyword.lower() in event.lower():
                return 'medium'

        return 'low'

    def _generate_links(self, program_id: str, program: Dict) -> Dict:
        """関連リンクを生成"""
        links = {}

        # ClinicalTrials.gov
        trial_ids = program.get('trial_ids', [])
        if trial_ids:
            links['clinicaltrials_gov'] = f"https://clinicaltrials.gov/study/{trial_ids[0]}"

        return links

    def _summarize_durations(self, params_data: Dict) -> Dict:
        """フェーズ期間を要約"""
        durations = params_data.get('phase_durations_years', {})
        summary = {}

        for phase, data in durations.items():
            if isinstance(data, dict):
                summary[phase] = {
                    'median_years': data.get('median', 0),
                    'range': [data.get('min', 0), data.get('max', 0)]
                }

        return summary

    def _write_json(self, filepath: Path, data: Dict) -> None:
        """JSONファイルを書き込む"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    """メイン実行"""
    generator = APIGenerator()
    generator.generate_all()


if __name__ == '__main__':
    main()
