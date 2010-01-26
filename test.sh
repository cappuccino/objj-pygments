find $1 -name "*.j" | while read f; do (echo $f >&2); python -m pygments -fhtml -O full -O encoding='utf-8' $f | grep "class=\"err\""; done

