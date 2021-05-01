from datetime import datetime, date
from typing import Union, Any, Callable
from aiomysql import Connection
from aiomysql.cursors import DictCursor
import aiomysql


class Svely:
    def __init__(self,
                 database: str,
                 user: str,
                 password: str,
                 port: int = 3306,
                 host: str = "localhost",
                 default_converter: Callable = None,
                 **kwargs
                 ):
        """
        :param database: Nome do banco de dados
        :param user: Usuário
        :param password: Senha do usuário
        :param port: Porta. Padrão: 3306
        :param host: Servidor. Padrão: "localhost"
        :param default_converter: Função personalizada para serializar as instâncias em inserts e updates. Você pode decidir como um datetime será convertido para string, por exemplo. O default é suficiente para a maioria dos casos
        :param kkwargs: Qualquer configuação desejável no inicializador de um banco de dados PyMySQL
        """
        self.credentials = {
            "db": database,
            "user": user,
            "password": password,
            "port": port,
            "host": host,
            **kwargs,
        }
        self._database: Union[Connection, None] = None
        self.converter = default_converter

    @property
    async def database(self):
        await self.open()
        return self._database

    @property
    def is_open(self):
        return self._database and not self._database.closed

    @property
    def is_close(self):
        return self._database is None or self._database.closed

    async def open(self):
        """
        Método que abre a conexão. Normalmente você não precisa executá-lo manualmente.
        """
        if self.is_close:
            self._database: Connection = await aiomysql.connect(**self.credentials)

    async def close(self):
        """
        Método que fecha a conexão. É uma boa prática fechar a conexão claramente quando ela não é mais útil.
        """
        if self.is_open:
            self._database.close()
            self._database.__del__()

    async def get_cursor(self) -> DictCursor:
        """
        :return: Cursor para querys. Retorna um DictCursor, muito útil para respostas em JSON.
        """
        if self.is_open:
            return await self._database.cursor(DictCursor)
        else:
            await self.open()
            return await self.get_cursor()

    async def select(self,
                     sql: str,
                     entity: Any = None,
                     unique: bool = False
                     ) -> Union[list, dict, Any, None]:
        """
        :param sql: Parte do comando APÓS a diretiva SELECT. Ex.: "* FROM table;"
        :param entity: Opcional. Construtor da instância que deva ser retornado. O padrão é uma lista de dicionários
        :param unique: Opcional. Indica que deve ser retornado apenas um dicionário ou instância personalizada
        :return: Se unique, retorna um dicionário ou a instância da classe indicada. Se não, retorna uma lista de
        dicionários ou de instâncias da classe indicada.
        """
        cursor = await self.get_cursor()
        await cursor.execute(f"SELECT {sql.replace(';', '')}{' LIMIT 1' if unique else ''};")
        if unique:
            dictionary = await cursor.fetchone()
            if dictionary:
                return entity(**dictionary) if entity else dictionary
            return None
        else:
            dictionaries = await cursor.fetchall()
            if dictionaries:
                return [entity(**item) for item in dictionaries] if entity else dictionaries
            return []

    async def insert(self,
                     table: str,
                     data: Union[dict, Any],
                     get_id: bool = False,
                     commit: bool = True,
                     ) -> Union[int, None]:
        """
        :param table: Nome da tabela
        :param data: Dados a serem inseridos em um dicionário ou entidade que possui __dict__ como propriedade
        :param get_id: Opcional. Indica se o ID do novo registro deve ser retornado. Não terá efeito a menos que
            commit = True.
        :param commit: Deve ou não realizar um commit imediato
        """
        cursor = await self.get_cursor()
        _fields, _values = _get_data(data, self.converter)

        sql = f"""
        INSERT INTO {table}
            ({','.join(_fields)})
            VALUES ({",".join(_values)});"""

        await cursor.execute(sql)

        result = None
        if get_id:
            await cursor.execute("SELECT LAST_INSERT_ID() as id;")
            new_id = (await cursor.fetchone())["id"]
            result = new_id

        if commit:
            await self._database.commit()
            await self.close()

        return result

    async def insert_many(self,
                          table: str,
                          data: list,
                          commit: bool = True,
                          ):
        """
        :param table: Nome da tabela
        :param data: Lista com dicionários ou entidades que possuem __dict__ como propriedade
        :param commit: Booleano que indica o commit imediato
        """
        cursor = await self.get_cursor()
        fields, values = _get_data(data, self.converter)
        sql = f"""
                INSERT INTO {table}
                    ({','.join(fields)})
                    VALUES {",".join([f'({",".join(row)})' for row in values])};"""
        print(sql)
        await cursor.execute(sql)
        if commit:
            await self._database.commit()

            await self.close()

    async def update(self,
                     table: str,
                     data: Union[dict, Any],
                     where: str,
                     commit: bool = True,
                     ):
        """
            :param table: Nome da tabela
            :param data: Dados a serem alterados em um dicionário ou entidade que possui __dict__ como propriedade
            :param where: Condição de update
            :param commit: Deve ou não realizar um commit imediato
        """
        cursor = await self.get_cursor()
        _fields, _data = _get_data(data, self.converter)
        real_values = dict(zip(_fields, _data))

        sql = f"""
            UPDATE {table}
            SET {','.join([f"{entry[0]} = {entry[1]}" for entry in real_values.items()])}
            {f"WHERE {where}" if where else ""};
        """
        await cursor.execute(sql)

        if commit:
            await self._database.commit()
            await self.close()

    async def delete(self,
                     table: str,
                     where: str,
                     commit: bool = True,
                     ):
        """
            :param table: Nome da tabela
            :param where: Condição de delete
            :param commit: Deve ou não realizar um commit imediato
        """
        cursor = await self.get_cursor()
        await cursor.execute(f"DELETE FROM {table}{f' WHERE {where}' if where else ''};")

        if commit:
            await self._database.commit()
            await self.close()

    async def sql(self, sql: str) -> DictCursor:
        cursor = await self.get_cursor()
        await cursor.execute(sql)
        return cursor

    async def commit(self):
        if self.is_open:
            await self._database.commit()

    async def rollback(self):
        if self.is_open:
            await self._database.rollback()

    async def is_empty(self, table: str, primary_key: str = None, where: str = None) -> bool:
        cursor = await self.get_cursor()
        await cursor.execute(f"SELECT {primary_key or '*'} FROM {table}{f' WHERE {where}' if where else ''} LIMIT 1")
        r = (await cursor.fetchone()) is None
        return r


def _get_data(data: Union[dict, Any, list], f) -> (list, list):
    """
    :param data: Dicionário de valores
    :return: Retorna fields(list), values(list) prontos para inserção no SQL
    """
    def converter(o) -> Union[str, int]:
        if isinstance(o, bool):
            return int(o)
        elif isinstance(o, (datetime, date)):
            return o.isoformat()
        return o.__str__().replace("'", "\\'")

    _fields = []
    _data = []
    if not isinstance(data, list):
        if not isinstance(data, dict):
            data = data.__dict__

        for par in data.items():
            if par[1] is not None:
                _fields.append(f"`{par[0]}`")
                new_value = (f or converter)(par[1])
                _data.append(f"'{new_value}'" if new_value != "__NULL__" else "NULL")
        return _fields, _data

    for item in data:
        value = []
        if not isinstance(item, dict):
            item = item.__dict__
        for par in item.items():
            if par[1] is not None:
                if not len(_data):
                    _fields.append(f"`{par[0]}`")

                new_value = converter(par[1])
                value.append(f"'{new_value}'" if new_value != "__NULL__" else "NULL")
        _data.append(value)
    return _fields, _data
