"""
数据库模块 - SQLite + SQLAlchemy
管理游戏历史记录
"""
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any

import yaml
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


def load_config():
    """加载配置"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def resolve_project_path(path_value: str) -> str:
    """Resolve config paths relative to the project root."""
    if os.path.isabs(path_value):
        return path_value

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.abspath(os.path.join(project_root, path_value))


def _dump_json(data: Any) -> str:
    return json.dumps(data if data is not None else None, ensure_ascii=False)


def _load_json(data: Optional[str], default: Any):
    if not data:
        return default
    return json.loads(data)


def _parse_datetime(value: Optional[str]) -> datetime:
    if isinstance(value, str) and value.strip():
        return datetime.fromisoformat(value)
    return datetime.now().astimezone()


class GameRecord(Base):
    """单表存储一局游戏完整历史记录。"""
    __tablename__ = 'game_history_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    schema_version = Column(String(20), nullable=False, default='1.0')
    external_game_id = Column(String(120), nullable=True, index=True)
    started_at = Column(DateTime, nullable=False, index=True)
    ended_at = Column(DateTime, nullable=True)
    end_status = Column(String(20), nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    num_players = Column(Integer, nullable=False)
    game_mode = Column(String(20), nullable=False, default='custom')
    path_length = Column(Integer, nullable=False, default=0)

    requested_config_json = Column(Text, nullable=False)
    resolved_config_json = Column(Text, nullable=False)
    players_json = Column(Text, nullable=False)
    action_history_json = Column(Text, nullable=False)
    final_player_remaining_json = Column(Text, nullable=False)
    final_scores_json = Column(Text, nullable=True)

    def to_dict(self, include_details: bool = False):
        data = {
            'id': self.id,
            'schema_version': self.schema_version,
            'game_id': self.external_game_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'end_status': self.end_status,
            'num_players': self.num_players,
            'game_mode': self.game_mode,
            'path_length': self.path_length,
        }

        if not include_details:
            return data

        requested_config = _load_json(self.requested_config_json, {})
        resolved_config = _load_json(self.resolved_config_json, {})
        players = _load_json(self.players_json, [])
        action_history = _load_json(self.action_history_json, [])
        final_player_remaining_ms = _load_json(self.final_player_remaining_json, [])
        final_scores = _load_json(self.final_scores_json, None)

        data.update({
            'error_message': self.error_message,
            'requested_config': requested_config,
            'resolved_config': resolved_config,
            'players': players,
            'action_history': action_history,
            'final_player_remaining_ms': final_player_remaining_ms,
            'final_scores': final_scores,
        })
        return data


class GameRepository:
    """游戏记录数据访问类"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        config = load_config()
        db_path = resolve_project_path(config['paths']['db_path'])

        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._initialized = True

    def create_game(self, game_data: Dict[str, Any]) -> int:
        """创建游戏记录"""
        session = self.Session()
        try:
            action_history = list(game_data.get('action_history', []) or [])
            record = GameRecord(
                schema_version=game_data.get('schema_version', '1.0'),
                external_game_id=game_data.get('game_id'),
                started_at=_parse_datetime(game_data.get('started_at')),
                ended_at=_parse_datetime(game_data.get('ended_at')) if game_data.get('ended_at') else None,
                end_status=game_data.get('end_status', 'finished'),
                error_message=game_data.get('error_message'),
                num_players=game_data.get('num_players', 3),
                game_mode=game_data.get('game_mode', 'custom'),
                path_length=game_data.get('path_length', len(action_history)),
                requested_config_json=_dump_json(game_data.get('requested_config', {})),
                resolved_config_json=_dump_json(game_data.get('resolved_config', {})),
                players_json=_dump_json(game_data.get('players', [])),
                action_history_json=_dump_json(action_history),
                final_player_remaining_json=_dump_json(game_data.get('final_player_remaining_ms', [])),
                final_scores_json=_dump_json(game_data.get('final_scores')),
            )
            session.add(record)
            session.commit()
            return record.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_game(self, game_id: int) -> Optional[Dict[str, Any]]:
        """获取单个游戏详情"""
        session = self.Session()
        try:
            game = session.query(GameRecord).filter_by(id=game_id).first()
            return game.to_dict(include_details=True) if game else None
        finally:
            session.close()

    def list_games(self, page=1, per_page=10, sort_by='started_at', sort_order='desc', filters=None):
        """获取游戏列表（分页）"""
        session = self.Session()
        try:
            query = session.query(GameRecord)

            if filters:
                if 'num_players' in filters:
                    query = query.filter(GameRecord.num_players == filters['num_players'])
                if 'end_status' in filters:
                    query = query.filter(GameRecord.end_status == filters['end_status'])
                if 'game_mode' in filters:
                    query = query.filter(GameRecord.game_mode == filters['game_mode'])

            sort_column_map = {
                'timestamp': GameRecord.started_at,
                'started_at': GameRecord.started_at,
                'ended_at': GameRecord.ended_at,
                'num_players': GameRecord.num_players,
                'path_length': GameRecord.path_length,
                'end_status': GameRecord.end_status,
            }
            sort_column = sort_column_map.get(sort_by, GameRecord.started_at)
            if sort_order == 'desc':
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())

            total = query.count()
            games = query.offset((page - 1) * per_page).limit(per_page).all()

            return {
                'games': [g.to_dict(include_details=False) for g in games],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'total_pages': (total + per_page - 1) // per_page,
                }
            }
        finally:
            session.close()

    def delete_game(self, game_id: int) -> bool:
        """删除游戏记录"""
        session = self.Session()
        try:
            game = session.query(GameRecord).filter_by(id=game_id).first()
            if game:
                session.delete(game)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_statistics(self):
        """获取统计信息"""
        session = self.Session()
        try:
            total_games = session.query(GameRecord).count()
            player_stats = session.query(
                GameRecord.num_players, func.count(GameRecord.id)
            ).group_by(GameRecord.num_players).all()

            return {
                'total_games': total_games,
                'player_distribution': {p[0]: p[1] for p in player_stats}
            }
        finally:
            session.close()


# 兼容旧名称
DatabaseManager = GameRepository
get_db_instance = GameRepository
