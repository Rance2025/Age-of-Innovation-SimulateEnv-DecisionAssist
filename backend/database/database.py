"""
数据库模块 - SQLite + SQLAlchemy
管理游戏历史记录
"""
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any

import yaml
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

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


class GameRecord(Base):
    """游戏记录主表"""
    __tablename__ = 'game_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    num_players = Column(Integer, nullable=False)
    setup_mode = Column(String(20), nullable=False)
    path_length = Column(Integer, default=0)
    setup_tile_args = Column(Text)
    setup_player_order_args = Column(Text)
    action_mode = Column(Text)

    action_history = relationship("ActionHistory", back_populates="game", cascade="all, delete-orphan")
    player_results = relationship("PlayerResult", back_populates="game", cascade="all, delete-orphan")

    def to_dict(self, include_details=False):
        data = {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'num_players': self.num_players,
            'setup_mode': self.setup_mode,
            'path_length': self.path_length,
            'created_at': self.timestamp.strftime('%Y-%m-%d %H:%M') if self.timestamp else None
        }
        if include_details:
            data['setup_tile_args'] = json.loads(self.setup_tile_args) if self.setup_tile_args else None
            data['setup_player_order_args'] = json.loads(self.setup_player_order_args) if self.setup_player_order_args else None
            data['action_mode'] = json.loads(self.action_mode) if self.action_mode else None
            data['action_history'] = [ah.to_dict() for ah in self.action_history]
            data['player_results'] = [pr.to_dict() for pr in self.player_results]
        return data


class ActionHistory(Base):
    """行动历史记录"""
    __tablename__ = 'action_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey('game_records.id'), nullable=False, index=True)
    sequence = Column(Integer, nullable=False)
    player_id = Column(Integer, nullable=False)
    action_type = Column(String(20), nullable=False)
    action_id = Column(Integer, nullable=False)

    game = relationship("GameRecord", back_populates="action_history")

    def to_dict(self):
        return {'player_id': self.player_id, 'action_type': self.action_type, 'action_id': self.action_id}


class PlayerResult(Base):
    """玩家结果"""
    __tablename__ = 'player_results'

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey('game_records.id'), nullable=False, index=True)
    player_id = Column(Integer, nullable=False)
    total_score = Column(Integer, nullable=False)
    board_score = Column(Integer, default=0)
    chain_score = Column(Integer, default=0)
    track_score = Column(Integer, default=0)
    resource_score = Column(Integer, default=0)

    game = relationship("GameRecord", back_populates="player_results")

    def to_dict(self):
        return {
            'player_id': self.player_id,
            'total': self.total_score,
            'board': self.board_score,
            'chain': self.chain_score,
            'track': self.track_score,
            'resource': self.resource_score
        }


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
            game = GameRecord(
                timestamp=datetime.fromisoformat(game_data.get('timestamp', datetime.now().isoformat())),
                num_players=game_data.get('num_players', 3),
                setup_mode=game_data.get('setup_mode', 'target'),
                path_length=game_data.get('path_length', 0),
                setup_tile_args=json.dumps(game_data.get('setup_tile_args', [])),
                setup_player_order_args=json.dumps(game_data.get('setup_player_order_args', [])),
                action_mode=json.dumps(game_data.get('action_mode', []))
            )
            session.add(game)
            session.flush()

            for idx, action in enumerate(game_data.get('action_history', [])):
                ah = ActionHistory(
                    game_id=game.id, sequence=idx, player_id=action[0],
                    action_type=action[1], action_id=action[2]
                )
                session.add(ah)

            result = game_data.get('result', {})
            for player_id, scores in result.items():
                pr = PlayerResult(
                    game_id=game.id, player_id=int(player_id),
                    total_score=scores.get('total', 0), board_score=scores.get('board', 0),
                    chain_score=scores.get('chain', 0), track_score=scores.get('track', 0),
                    resource_score=scores.get('resource', 0)
                )
                session.add(pr)

            session.commit()
            return game.id
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

    def list_games(self, page=1, per_page=10, sort_by='timestamp', sort_order='desc', filters=None):
        """获取游戏列表（分页）"""
        session = self.Session()
        try:
            query = session.query(GameRecord)

            if filters:
                if 'num_players' in filters:
                    query = query.filter(GameRecord.num_players == filters['num_players'])
                if 'setup_mode' in filters:
                    query = query.filter(GameRecord.setup_mode == filters['setup_mode'])

            sort_column = getattr(GameRecord, sort_by, GameRecord.timestamp)
            if sort_order == 'desc':
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())

            total = query.count()
            games = query.offset((page - 1) * per_page).limit(per_page).all()

            return {
                'games': [g.to_dict(include_details=False) for g in games],
                'pagination': {
                    'page': page, 'per_page': per_page, 'total': total,
                    'total_pages': (total + per_page - 1) // per_page
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
