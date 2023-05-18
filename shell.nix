{ nixpkgs ? import <nixpkgs> {} }:

nixpkgs.mkShell {
  buildInputs = [
    nixpkgs.poetry
    nixpkgs.gh
    nixpkgs.docker-compose
    nixpkgs.alembic
    nixpkgs.pam
    nixpkgs.postgresql
  ];
}

