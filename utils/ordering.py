"""Gestion intelligente des ordres d'affichage uniques."""


def _active_clause(soft_delete):
    if soft_delete:
        return " AND (deleted_at IS NULL OR deleted_at = '')"
    return ""


def next_free_order(cursor, table, order_column='order_index', soft_delete=True):
    """Retourne le plus petit entier >= 0 non utilisé, ou max+1 si la plage est dense."""
    where = f"WHERE 1=1{_active_clause(soft_delete)}"
    cursor.execute(
        f'SELECT {order_column} FROM {table} {where} ORDER BY {order_column} ASC'
    )
    used = {int(row[0] or 0) for row in cursor.fetchall()}
    candidate = 0
    while candidate in used:
        candidate += 1
    return candidate


def claim_unique_order(
    cursor,
    table,
    desired_order,
    exclude_id=None,
    order_column='order_index',
    soft_delete=True,
):
    """
    Garantit que `desired_order` n'est possédé que par la ligne `exclude_id`
    (ou sera libre pour une création).

    - En mise à jour : échange avec le conflit si possible (l'autre reçoit l'ancien ordre).
    - Sinon : déplace chaque conflit vers le prochain numéro libre.
    - En création : déplace les conflits vers le prochain numéro libre.

    Returns:
        tuple: (ordre final pour la cible, liste de {id, order} déplacés)
    """
    try:
        target = int(desired_order)
    except (TypeError, ValueError):
        target = 0
    if target < 0:
        target = 0

    active = _active_clause(soft_delete)
    shifts = []

    previous_order = None
    if exclude_id is not None:
        cursor.execute(
            f'SELECT {order_column} FROM {table} WHERE id = ?{active}',
            (int(exclude_id),),
        )
        row = cursor.fetchone()
        if row is not None:
            previous_order = int(row[0] or 0)
            if previous_order == target:
                return target, shifts

    params = [target]
    exclude_sql = ''
    if exclude_id is not None:
        exclude_sql = ' AND id != ?'
        params.append(int(exclude_id))

    cursor.execute(
        f'''
        SELECT id, {order_column} FROM {table}
        WHERE {order_column} = ?{exclude_sql}{active}
        ORDER BY id ASC
        ''',
        params,
    )
    conflicts = cursor.fetchall()
    if not conflicts:
        return target, shifts

    # Premier conflit : échange avec l'ancien ordre de la cible si disponible
    first = conflicts[0]
    conflict_id = int(first[0])
    swap_to = previous_order

    if swap_to is None or swap_to == target:
        swap_to = None
    else:
        # Vérifier que swap_to n'est pas déjà pris par un autre (hors cible/conflit)
        cursor.execute(
            f'''
            SELECT id FROM {table}
            WHERE {order_column} = ? AND id != ? AND id != ?{active}
            LIMIT 1
            ''',
            (swap_to, conflict_id, int(exclude_id) if exclude_id is not None else -1),
        )
        if cursor.fetchone():
            swap_to = None

    if swap_to is None:
        # Place temporaire pour libérer `target`, puis numéro libre définitif
        cursor.execute(
            f'SELECT COALESCE(MAX({order_column}), 0) FROM {table} WHERE 1=1{active}'
        )
        temp = int(cursor.fetchone()[0] or 0) + 1000
        cursor.execute(
            f'UPDATE {table} SET {order_column} = ? WHERE id = ?',
            (temp, conflict_id),
        )
        free = next_free_order(cursor, table, order_column, soft_delete)
        cursor.execute(
            f'UPDATE {table} SET {order_column} = ? WHERE id = ?',
            (free, conflict_id),
        )
        shifts.append({'id': str(conflict_id), 'order': free})
    else:
        cursor.execute(
            f'UPDATE {table} SET {order_column} = ? WHERE id = ?',
            (swap_to, conflict_id),
        )
        shifts.append({'id': str(conflict_id), 'order': swap_to})

    # Conflits supplémentaires (données déjà dupliquées) → numéros libres
    for conflict in conflicts[1:]:
        cid = int(conflict[0])
        cursor.execute(
            f'SELECT COALESCE(MAX({order_column}), 0) FROM {table} WHERE 1=1{active}'
        )
        temp = int(cursor.fetchone()[0] or 0) + 1000
        cursor.execute(
            f'UPDATE {table} SET {order_column} = ? WHERE id = ?',
            (temp, cid),
        )
        free = next_free_order(cursor, table, order_column, soft_delete)
        cursor.execute(
            f'UPDATE {table} SET {order_column} = ? WHERE id = ?',
            (free, cid),
        )
        shifts.append({'id': str(cid), 'order': free})

    return target, shifts
