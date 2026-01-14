# Telegram Bot Financeiro

Bot de Telegram para gestão financeira pessoal.


## Comandos


### Entrada
```
/entra <valor>
/entra <valor> <tipo>
/entra <valor> <tipo> <tag1> <tag2> ... <tagN>

/entra 1512 fixo trabalho
```
Coloca valor positivo no balanço financeiro no momento da mensagem. O tipo e as tags são para organização nos relatórios.  
A transação recém criada fica selecionada para alterações desejadas.


### Saída
```
/sai <valor>
/sai <valor> <tipo>
/sai <valor> <tipo> <tag1> <tag2> ... <tagN>

/sai 25.75 variável alimentação
```
Coloca valor negativo no balanço financeiro no momento da mensagem. As tags são para organização nos relatórios.  
A transação recém criada fica selecionada para alterações desejadas.


### Saldo
```
/saldo
/saldo <mês>
/saldo <mês_inicial> <mês_final>
/saldo <ano> <mês_inicial> <mês_final>
/saldo <ano_inicial> <mês_inicial> <ano_final> <mês_final>
```
Retorna o saldo do intervalo de mesês especificado. Quando usado sem argumentos, retorna o saldo do mês corrente.


### Extrato
```
/extrato
/extrato <mês>
/extrato <mês_inicial> <mês_final>
/extrato <ano> <mês_inicial> <mês_final>
/extrato <ano_inicial> <mês_inicial> <ano_final> <mês_final>
```
Retorna o extrato ou histórico de transações do intervalo de mesês especificado. Quando usado sem argumentos, retorna o extrato do mês corrente.


### Ver e selecionar transação
```
/ver
/ver <ano> <mês> <dia> <hora-min-sec>

/ver 2026 1 10 143753
```
Exibe e seleciona uma transação, caso ela exista.  
Quando invocada sem argumentos, exibe a transação selecionada.


### Alterar valor da transação
```
/valor <novo_valor>
```
Atualiza o valor da transação selecionada.
Aceita valores negativos (para saída) e positivos (para entrada).


### Alterar tipo da transação
```
/tipo <tipo_da_transação>
```
Atualiza o tipo da transação selecionada.  
Somente tipos registrados são aceitos. Os tipos default são de transação `fixa` e `variável`.  
Tipos podem ser criados e removidos com o comando `/tipos`, explicado mais adiante.


### Alterar tags da transação
```
/tag <tag_adicionar>
/tag -<tag_remover>
/tag <tag1> <tag2> -<tag3> ...
```
Adiciona e remove tags na transação selecionada. Usar `/tag ferramentas -outros` vai pegar a transação selecionada, adicionar a tag `ferramentas` e remover a tag `outros`.


### Alterar descrição da transação
```
/detalhes Mensagem explicando a última movimentação financeira.
```
Adiciona uma descrição informativa à transação selecionada, substituindo a descrição atual caso haja.


### Tipos de transações
```
/tipos
/tipos adi <novo_tipo_1> <novo_tipo_2> ...
/tipos rem <tipo_a_remover_1> <tipo_a_remover_2> ...
```
Exibe os tipos registrados e disponíveis para uso.  
Usar `/tipos adi` serve para adicionar novos tipos para as transações.  
User `/tipos rem` serve para remover tipos indesejados para as transações.


### Tags de transações
```
/tags
/tags adi <nova_tag_1> <nova_tag_2> ...
/tags rem <tag_a_remover_1> <tag_a_remover_2> ...
```
Exibe as tags registradas e disponíveis para uso.  
Usar `/tags adi` serve para adicionar novas tags para as transações.  
User `/tags rem` serve para remover tags indesejadas para as transações.

