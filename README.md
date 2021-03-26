# Svely

### Camada de abstração para projetos Python assíncronos com chamadas a bancos MySQL
***
## Principais recursos:

- Chamadas a bancos MySQL de forma totalmente assíncrona
- Facilidade para abrir e gerenciar conexões
- Suporte a entidades para agir como um micro ORM
***
## Versão
- 0.1
***
## Dependência
- AIOMySQL
***
## Requerimento
Python >= 3.6
***
## Licença
MIT
***
## Instalação
1. Clone este repositório

    <code>git clone https://github.com/vthiagossilva/svely.git</code>

2. Instale a dependência

    <code>pip install -r requirements.txt</code>

***
## Exemplo de uso

Svely foi pensado para trabalhar com conexões não bloqueantes, então pode ser uma boa ideia preparar uma função nos níveis mais altos do seu código para criar novas conexões.

<code><pre>
from settings import credentials
from svely import Svely<br>

def get_svely(): Svely(**credentials)</pre>
</code>

Em seguida você pode instancia-lo em qualquer lugar, como em um controller de requisição web, por exemplo.

<code><pre>
from ... import get_svely
...

async def some_function():
&emsp;my_svely = get_svely()
&emsp;result = await my_svely.select("* from users")
&emsp;print(result)
&emsp;await my_svely.close()
</pre></code>

Um uso bem interessante é quando se trabalha com entidades. Digamos que você possua a seguinte classe:
<code><pre>
class User:
&emsp;def \_\_init\_\_(self, name: str, email: str, created_at: datetime):
&emsp;&emsp;self.name = name
&emsp;&emsp;self.email = email
&emsp;&emsp;self.created_at = created_at
</pre></code>
Você pode informar essa classe no método __select()__ de __my_svely__ para indicar que o resultado deve ser uma lista de objetos Users já instanciados.
<br><code>result = await my_svely.select("* from users", entity=Users)</code><br>
<p>O contrário também é válido e é possível passar entidades como dados para os métodos de escrita como <b>insert()</b> e <b>update()</b> Naturalmente, se os atributos não corresponderem aos campos no banco de dados uma exceção <b>ValueError</b> será disparada.</p>
<p>Atualmente é possível utilizar entidades cujos atributos possam ser acessados como dicionários pela propriedade interna <b>.__dict__</b>.</p>
<hr>
<h2>Referências da API</h2>
<h3>Svely.__init__(...)</h3>
<ul>
<li>database: str, nome do banco de dados</li>
<li>user: str, usuário</li>
<li>password: str, senha do usuário para o banco</li>
<li>host: str = "localhost", URL do servidor</li>
<li>port: int = 3306, porta da rede</li>
<li>default_converter: Callable = None, Função personalizada para serializar as instâncias em inserts e updates. Você pode decidir como um datetime será convertido para string, por exemplo. O default é suficiente para a maioria dos casos</li>
<li>**kkwargs: Qualquer configuação desejável no inicializador de um banco de dados PyMySQL</li>
</ul><br>
<h3>Propriedade: Svely.is_open -> bool</h3>
Retorna um booleano que indica se a conexão está aberta.<br>
<h3>Propriedade: Svely.is_close -> bool</h3>
Retorna um booleano que indica se a conexão está fechada.<br>
<h3>Propriedade: Svely.database</h3>
Retorna uma instância de objeto banco de dados PyMySQL com conexão seguramente aberta.

<br><h2>Todos os métodos abaixo são aguardáveis (corrotinas) e precisam ser chamados com await ou create_task()</h2>
<h3>Método: Svely.open()</h3>
<p>Abre a conexão. Normalmente você não deve executá-lo manualmente pois a primeira operação de leitura ou escrita.</p><br>

<h3>Método: Svely.close()</h3>
<p>Facha a conexão. É <b>imprescindível</b> que a conexão seja claramente fechada quando esta não é mais necessária</p><br>

<h3>Método: Svely.select(...)</h3>
<p>Obter registros como dicionários ou entidades</p>
<ul>
<li>sql: str. Parte do comando APÓS a diretiva SELECT. Ex.: "* FROM table;"</li>
<li>entity: class, Opcional. Construtor da instância que deva ser retornado. O padrão é uma lista de dicionários</li>
<li>unique: bool, Opcional. Indica que deve ser retornado apenas um dicionário ou instância personalizada</li>
<li><b>return</b>: Se unique, retorna um dicionário ou a instância da classe indicada. Se não, retorna uma lista de
        dicionários ou de instâncias da classe indicada.</li>
</ul><br>

<h3>Método: Svely.insert(...)</h3>
<p>Inserir um registro</p>
<ul>
<li>table: str. Nome da tabela</li>
<li>data: dict, Any. Dados a serem inseridos em um dicionário ou entidade que possui __dict__ como propriedade</li>
<li>get_id: bool, Opcional. Indica se o ID do novo registro deve ser retornado. Não terá efeito a menos que commit = True.</li>
<li>commit: bool = True. Deve ou não realizar um commit imediato</li>
</ul><br>

<h3>Método: Svely.insert_many(...)</h3>
<p>Inserir muitos registros</p>
<ul>
<li>table: str. Nome da tabela</li>
<li>data: list, Any. Dados a serem inseridos em uma lista de dicionários ou entidades</li>
<li>commit: bool = True. Deve ou não realizar um commit imediato</li>
</ul><br>

<h3>Método: Svely.update(...)</h3>
<p>Atualizar um registro</p>
<ul>
<li>table: str. Nome da tabela</li>
<li>data: dict, Any. Dados a serem inseridos em um dicionário ou entidade</li>
<li>where: str. Linha de where clause para update. Passe uma string vazia para atualizar todos os registros.</li>
<li>commit: bool = True. Deve ou não realizar um commit imediato</li>
</ul><br>

<h3>Método: Svely.delete(...)</h3>
<p>Deletar registros</p>
<ul>
<li>table: str. Nome da tabela</li>
<li>where: str. Linha de where clause para delete. Passe uma string vazia para deletar todos os registros.</li>
<li>commit: bool = True. Deve ou não realizar um commit imediato</li>
</ul><br>

<h3>Método: Svely.is_empty(...) -> bool</h3>
<p>Verifica se a pesquisa não retorna registro. Se where não é passado, indica se a tabela está vazia.</p>
<ul>
<li>table: str. Nome da tabela</li>
<li>primary_key: str, Opcional. Indicar uma chave primária torna a pesquisa mais eficiente</li>
<li>where: str. Clausula where.</li>
</ul><br>

<h3>Método: Svely.sql(sql: str) -> DictCursor</h3>
<p>Executa um SQL raw e retorna um objeto DictCursor</p><br>

<h3>Método: Svely.commit()</h3>
<p>Realiza um commit de alterações</p><br>

<h3>Método: Svely.rollback()</h3>
<p>Executa um rollback do que foi feito na conexão atual, posteriaor a qualquer commit</p><br>
