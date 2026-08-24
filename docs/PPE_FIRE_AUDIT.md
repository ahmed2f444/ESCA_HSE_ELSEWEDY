# PPE and Fire submission audit

## Verdict

The submission is retained under `imports/` as read-only integration evidence.
Its domain code is useful, but the project must not be promoted directly to the
canonical backend without configuration and test fixes.

## Included capabilities

- Fire equipment inventory and inspection records.
- Fixed safety assets.
- PPE inventory, assignment matrix and stock transactions.
- REST controllers, services, repositories, entities and controller tests.

## Findings

- Source compilation succeeds with Java 17.
- The test suite executes 33 tests: 11 pass and 22 fail while loading the
  Spring application context.
- The common failure is Hibernate being initialized without usable JDBC
  metadata after the tests exclude the data source configuration.
- Local database credentials were embedded in the submitted configuration.
- Both PostgreSQL and MySQL drivers are present even though the unified system
  has standardized on MySQL.
- Schema mutation and seed loading are enabled automatically.
- Controllers allow every CORS origin.

## Canonical integration requirements

1. Load every secret from environment variables.
2. Keep only the MySQL runtime driver.
3. Replace implicit schema mutation with versioned migrations.
4. Run seed data only through an explicit local development profile.
5. Configure CORS centrally from an allow-list.
6. Port the useful domain classes into the accepted backend package structure.
7. Repair controller tests so each test slice has a consistent persistence
   strategy or fully mocked service boundary.
