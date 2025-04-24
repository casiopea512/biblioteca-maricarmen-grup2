#!/bin/bash

REACT_FOLDER=react
echo "Construint projecte React..."
cd $REACT_FOLDER
npm install
npm run build
cd ..

echo "Transferint arxius estàtics al projecte Django"
mkdir -p biblioteca/templates
mkdir -p biblioteca/static
cp $REACT_FOLDER/dist/index.html biblioteca/templates/index.html
cp -r $REACT_FOLDER/dist/static biblioteca/

echo "Transferint arxius d'errors al projecte Django"
cp $REACT_FOLDER/dist/errors/404.html biblioteca/templates/404.html
cp $REACT_FOLDER/dist/errors/403.html biblioteca/templates/403.html

echo "Desplegament finalitzat."
echo "Pots posar en marxa el servidor amb './manage.py runserver'"
