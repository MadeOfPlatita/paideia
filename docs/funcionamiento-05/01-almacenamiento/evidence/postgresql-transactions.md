# Extracto de documentación primaria

URL: https://www.postgresql.org/docs/current/tutorial-transactions.html
Título: 3.4. Transactions

Transactions are a fundamental concept of all database systems. The essential point is that it bundles multiple steps into a single, all-or-nothing operation. The intermediate states between the steps are not visible to other concurrent transactions, and if some failure occurs that prevents the transaction from completing, then none of the steps affect the database at all.

A transactional database guarantees that all the updates made by a transaction are logged in permanent storage (i.e., on disk) before the transaction is reported complete.
