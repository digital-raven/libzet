all:
	python3 -m build

release:
	twine upload -r pypi dist/*

clean:
	rm -rf libzet.egg-info dist
