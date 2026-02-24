# Changelog

All notable changes to this project will be documented in this file.

## [4.0.0] - 2025-08-12
### Added
- Complete rewrite of backend with PostgreSQL and `skatetrax_core` package.
- New REST API endpoints designed for modern frontend integration.
- Major refactor of data models and database schema.
- Secure user authentication with Flask and hashed passwords.
- React-based frontend planned with clean API separation.
- Containerization considerations.

### Changed
- Dropped backward compatibility with v3.x and earlier versions.
- Removed legacy PHP and MySQL codebase.
- Redesigned app structure and module imports for clarity and scalability.

### Removed
- Legacy UI components incompatible with new API.
- Deprecated database tables and outdated data formats.

---

## Versioning Guidance

We follow [Semantic Versioning](https://semver.org/) (SemVer):

- **MAJOR version (X.y.z)**  
  Increment when you make incompatible API changes or major rewrites that break backward compatibility (like now going from v3 → v4).

- **MINOR version (x.Y.z)**  
  Increment when you add functionality in a backward-compatible manner. Examples: new endpoints, new features, performance improvements without breaking changes.

- **PATCH version (x.y.Z)**  
  Increment when you make backward-compatible bug fixes. Examples: fixing typos, patching security vulnerabilities, small code refactors without changing API behavior.

---

## Example future versions

- 4.0.1 → Bug fix release after 4.0.0 production launch.
- 4.1.0 → Add new API endpoints or frontend features without breaking current clients.
- 5.0.0 → Another major rewrite that breaks backward compatibility.