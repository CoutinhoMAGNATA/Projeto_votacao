import sqlite3
import hashlib
from datetime import datetime

class Database:
    def __init__(self, db_name='eleicao.db'):
        self.db_name = db_name
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabela de candidatos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS candidatos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                partido TEXT NOT NULL,
                numero INTEGER UNIQUE NOT NULL,
                cargo TEXT NOT NULL,
                votos INTEGER DEFAULT 0,
                ativo BOOLEAN DEFAULT TRUE,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de usuários/eleitores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cpf TEXT UNIQUE NOT NULL,
                nome TEXT NOT NULL,
                email TEXT,
                ja_votou BOOLEAN DEFAULT FALSE,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de votos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS votos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_cpf TEXT NOT NULL,
                candidato_id INTEGER NOT NULL,
                data_voto TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_cpf) REFERENCES usuarios (cpf),
                FOREIGN KEY (candidato_id) REFERENCES candidatos (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # CRUD para Candidatos
    def criar_candidato(self, nome, partido, numero, cargo):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO candidatos (nome, partido, numero, cargo)
                VALUES (?, ?, ?, ?)
            ''', (nome, partido, numero, cargo))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def listar_candidatos(self, ativo=True):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM candidatos WHERE ativo = ? ORDER BY cargo, numero
        ''', (ativo,))
        candidatos = cursor.fetchall()
        conn.close()
        return candidatos
    
    def atualizar_candidato(self, candidato_id, nome, partido, numero, cargo):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE candidatos 
                SET nome = ?, partido = ?, numero = ?, cargo = ?
                WHERE id = ?
            ''', (nome, partido, numero, cargo, candidato_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def excluir_candidato(self, candidato_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE candidatos SET ativo = FALSE WHERE id = ?', (candidato_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    
    # Gerenciamento de Usuários
    def criar_usuario(self, cpf, nome, email=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO usuarios (cpf, nome, email)
                VALUES (?, ?, ?)
            ''', (cpf, nome, email))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def verificar_usuario_ja_votou(self, cpf):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT ja_votou FROM usuarios WHERE cpf = ?', (cpf,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    # Sistema de Votação
    def registrar_voto(self, usuario_cpf, candidato_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Iniciar transação
            cursor.execute('BEGIN TRANSACTION')
            
            # Registrar o voto
            cursor.execute('''
                INSERT INTO votos (usuario_cpf, candidato_id)
                VALUES (?, ?)
            ''', (usuario_cpf, candidato_id))
            
            # Atualizar contador de votos do candidato
            cursor.execute('''
                UPDATE candidatos 
                SET votos = votos + 1 
                WHERE id = ?
            ''', (candidato_id,))
            
            # Marcar usuário como já votou
            cursor.execute('''
                UPDATE usuarios 
                SET ja_votou = TRUE 
                WHERE cpf = ?
            ''', (usuario_cpf,))
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    # Relatórios e Estatísticas
    def obter_resultados(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.cargo, c.nome, c.partido, c.numero, c.votos
            FROM candidatos c
            WHERE c.ativo = TRUE
            ORDER BY c.cargo, c.votos DESC
        ''')
        resultados = cursor.fetchall()
        conn.close()
        return resultados
    
    def total_eleitores(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM usuarios')
        total = cursor.fetchone()[0]
        conn.close()
        return total
    
    def total_votos(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM votos')
        total = cursor.fetchone()[0]
        conn.close()
        return total