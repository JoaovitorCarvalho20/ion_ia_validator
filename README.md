# Validador de Regras — ION IA

Aplicação desktop (Python + Tkinter) para inspecionar, de forma visual e rápida, as regras de **antecedentes** e **consequentes** geradas pelo módulo de IA do ION.

## Motivação

Durante a implantação do ION IA, a validação das regras geradas (tabelas `ionv_rules_antecedents` e `ionv_rules_consequents`) era feita manualmente via consultas SQL diretas na base `.db`/`.s3db` do cliente. Esse processo era lento, propenso a erro e exigia conhecimento de SQL de quem estava validando.

Esta ferramenta foi criada para dar ao **time de implantação** uma forma prática e visual de:

- Confirmar se o módulo de IA já gerou as tabelas de regras na base do cliente;
- Ver rapidamente o total de regras criadas;
- Identificar quantas regras possuem **inteligência comercial** associada e quantas não possuem;
- Explorar, filtrar e ordenar as regras (antecedentes, consequente, quantidade de antecedentes) sem escrever uma única query.

Isso reduz o tempo de validação em campo e evita que problemas de geração de regras só sejam percebidos depois da implantação concluída.

## O que a ferramenta faz

1. **Carrega uma base SQLite** do cliente (`.db`, `.s3db`, `.sqlite`, `.sqlite3`).
2. **Verifica a existência** das tabelas `ionv_rules_antecedents` e `ionv_rules_consequents`. Se alguma estiver ausente, avisa que o módulo de IA pode ainda não ter sido executado.
3. **Consolida as regras**, agrupando os antecedentes de cada `rule_id` e cruzando com o respectivo consequente e a flag de inteligência comercial.
4. Exibe cartões de resumo:
   - Total de regras
   - Regras com inteligência comercial
   - Regras sem inteligência comercial
   - Status das tabelas (OK / Ausente)
5. Lista as regras em uma tabela navegável, com:
   - Filtro de texto livre (busca em qualquer coluna)
   - Filtro por inteligência comercial (Todos / Com IC / Sem IC)
   - Ordenação por coluna (clique no cabeçalho)

## Como usar

```bash
python ion_ia_validator.py
```

1. Clique em **"⬆ Carregar base (.db / .s3db)"** e selecione a base SQLite do cliente.
2. Confira os cartões de métricas no topo para uma visão geral da geração de regras.
3. Use o campo de filtro e os radio buttons de IC para localizar regras específicas.
4. Clique nos cabeçalhos da tabela para ordenar por qualquer coluna.

## Requisitos

- Python 3.x
- Tkinter (incluso na instalação padrão do Python no Windows)
- Nenhuma dependência externa além da biblioteca padrão (`sqlite3`, `tkinter`)
