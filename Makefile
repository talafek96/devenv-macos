.PHONY: help setup update lint test check clean release

.DEFAULT_GOAL := help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

setup: ## Run the full environment setup (idempotent)
	@bash setup.sh

update: ## Alias for setup — re-runs everything, upgrading outdated brew packages
	@bash setup.sh

lint: ## Lint shell scripts + validate Python syntax
	@echo "Linting shell scripts..."
	@command -v shellcheck >/dev/null 2>&1 && shellcheck setup.sh bootstrap.sh || echo "  (shellcheck not installed — skipping; brew install shellcheck)"
	@echo "Checking Python syntax..."
	@python3 -m py_compile setup.py
	@find devenv -name '*.py' -exec python3 -m py_compile {} +
	@echo "All lint checks passed."

test: ## Validate scripts + module discovery + config files
	@echo "Checking bash syntax..."
	@bash -n setup.sh bootstrap.sh
	@echo "Checking Python module discovery..."
	@python3 -c "import sys; sys.path.insert(0,'.'); from devenv.modules import discover_modules; m=discover_modules(); print(f'{len(m)} modules: '+', '.join(x.name for x in m))"
	@echo "Validating karabiner.json..."
	@plutil -convert json -o /dev/null dotfiles/config/karabiner/karabiner.json && echo "  karabiner.json OK"
	@echo "All checks passed."

check: lint test ## Run all quality checks

clean: ## Remove backup files created by setup
	@echo "Removing *.devenv-backup.* files from ~/"
	@find $(HOME) -maxdepth 1 -name '*.devenv-backup.*' -print -delete 2>/dev/null || true
	@echo "Done."

release: ## Tag a release (vYYYY.MM.DD or vYYYY.MM.DD-N) and push
	@TODAY=$$(date -u +%Y.%m.%d); \
	EXISTING=$$(git tag -l "v$$TODAY" "v$$TODAY-*" | sort -V); \
	if [ -z "$$EXISTING" ]; then TAG="v$$TODAY"; \
	else LAST=$$(echo "$$EXISTING" | tail -1); \
		if [ "$$LAST" = "v$$TODAY" ]; then TAG="v$$TODAY-1"; \
		else N=$$(echo "$$LAST" | sed "s/v$$TODAY-//"); TAG="v$$TODAY-$$((N + 1))"; fi; \
	fi; \
	echo "Tagging: $$TAG"; git tag "$$TAG"; git push origin "$$TAG"
