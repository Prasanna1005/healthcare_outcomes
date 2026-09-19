{% macro safe_divide(numerator, denominator) %}
    case
        when {{ denominator }} = 0
          or {{ denominator }} is null
        then null
        else ({{ numerator }})::float / ({{ denominator }})::float
    end
{% endmacro %}


{% macro create_run_history_table_if_not_exists() %}
    {% set sql %}
        create table if not exists {{ target.database }}.META.dbt_run_history (
            invocation_id    varchar(64),
            run_started_at   timestamp_ltz,
            run_completed_at timestamp_ltz,
            target_name      varchar(64),
            command          varchar(64),
            status           varchar(32),
            num_models_total number,
            num_models_pass  number,
            num_models_fail  number,
            num_models_warn  number,
            execution_time_s number(12, 3)
        )
    {% endset %}

    {% if execute %}
        {% do run_query(sql) %}
    {% endif %}
{% endmacro %}


{% macro insert_run_history_row(results) %}
    {% if execute %}

        {% set total = results | length %}

        {% set passes =
            results
            | selectattr('status', 'equalto', 'success')
            | list
            | length
        %}

        {% set fails =
            results
            | selectattr('status', 'equalto', 'error')
            | list
            | length
        %}

        {% set warns =
            results
            | selectattr('status', 'equalto', 'warn')
            | list
            | length
        %}

        {% set elapsed = results | sum(attribute='execution_time') %}

        {% set sql %}
            insert into {{ target.database }}.META.dbt_run_history
            (
                invocation_id,
                run_started_at,
                run_completed_at,
                target_name,
                command,
                status,
                num_models_total,
                num_models_pass,
                num_models_fail,
                num_models_warn,
                execution_time_s
            )
            select
                '{{ invocation_id }}',
                '{{ run_started_at }}',
                current_timestamp(),
                '{{ target.name }}',
                '{{ flags.WHICH }}',
                case
                    when {{ fails }} > 0 then 'error'
                    when {{ warns }} > 0 then 'warn'
                    else 'success'
                end,
                {{ total }},
                {{ passes }},
                {{ fails }},
                {{ warns }},
                {{ elapsed | round(3) }}
        {% endset %}

        {% do run_query(sql) %}

    {% endif %}
{% endmacro %}


{% macro apply_masking_policies_to_dim_patient() %}
    {% if execute and flags.WHICH == 'run' %}

        {# -------------------------------------------------------------
           1. Check whether DIM_PATIENT exists
           ------------------------------------------------------------- #}

        {% set check_sql %}
            select count(*)
            from {{ target.database }}.information_schema.tables
            where table_schema = 'MARTS'
              and table_name = 'DIM_PATIENT'
        {% endset %}

        {% set result = run_query(check_sql) %}

        {% if result and result[0][0] | int > 0 %}

            {% do log(
                "DIM_PATIENT exists. Applying governance policies.",
                info=True
            ) %}


            {# ---------------------------------------------------------
               2. Apply masking policy to FIRST_NAME
               --------------------------------------------------------- #}

            {% set masking_sql_1 %}
                alter table {{ target.database }}.MARTS.DIM_PATIENT
                modify column first_name
                set masking policy
                {{ target.database }}.GOVERNANCE.mask_full_name
            {% endset %}

            {% do run_query(masking_sql_1) %}


            {# ---------------------------------------------------------
               3. Apply masking policy to LAST_NAME
               --------------------------------------------------------- #}

            {% set masking_sql_2 %}
                alter table {{ target.database }}.MARTS.DIM_PATIENT
                modify column last_name
                set masking policy
                {{ target.database }}.GOVERNANCE.mask_full_name
            {% endset %}

            {% do run_query(masking_sql_2) %}


            {# ---------------------------------------------------------
               4. Apply masking policy to MRN
               --------------------------------------------------------- #}

            {% set masking_sql_3 %}
                alter table {{ target.database }}.MARTS.DIM_PATIENT
                modify column mrn
                set masking policy
                {{ target.database }}.GOVERNANCE.mask_mrn
            {% endset %}

            {% do run_query(masking_sql_3) %}


            {# ---------------------------------------------------------
               5. Apply masking policy to DATE_OF_BIRTH
               --------------------------------------------------------- #}

            {% set masking_sql_4 %}
                alter table {{ target.database }}.MARTS.DIM_PATIENT
                modify column date_of_birth
                set masking policy
                {{ target.database }}.GOVERNANCE.mask_dob_to_year
            {% endset %}

            {% do run_query(masking_sql_4) %}


            {# ---------------------------------------------------------
               6. Apply masking policy to PHONE_NUMBER
               --------------------------------------------------------- #}

            {% set masking_sql_5 %}
                alter table {{ target.database }}.MARTS.DIM_PATIENT
                modify column phone_number
                set masking policy
                {{ target.database }}.GOVERNANCE.mask_phone
            {% endset %}

            {% do run_query(masking_sql_5) %}


            {# ---------------------------------------------------------
               7. Apply masking policy to EMAIL
               --------------------------------------------------------- #}

            {% set masking_sql_6 %}
                alter table {{ target.database }}.MARTS.DIM_PATIENT
                modify column email
                set masking policy
                {{ target.database }}.GOVERNANCE.mask_email
            {% endset %}

            {% do run_query(masking_sql_6) %}


            {# ---------------------------------------------------------
               8. Apply masking policy to ADDRESS_LINE1
               --------------------------------------------------------- #}

            {% set masking_sql_7 %}
                alter table {{ target.database }}.MARTS.DIM_PATIENT
                modify column address_line1
                set masking policy
                {{ target.database }}.GOVERNANCE.mask_address
            {% endset %}

            {% do run_query(masking_sql_7) %}


            {# ---------------------------------------------------------
               9. Apply masking policy to ADDRESS_POSTAL_CODE
               --------------------------------------------------------- #}

            {% set masking_sql_8 %}
                alter table {{ target.database }}.MARTS.DIM_PATIENT
                modify column address_postal_code
                set masking policy
                {{ target.database }}.GOVERNANCE.mask_postal_code_to_3digit
            {% endset %}

            {% do run_query(masking_sql_8) %}


            {% do log(
                "Masking policies applied to DIM_PATIENT.",
                info=True
            ) %}


            {# ---------------------------------------------------------
               10. Check existing ROW ACCESS POLICY
               --------------------------------------------------------- #}

            {% set row_policy_check_sql %}
                select count(*)
                from table(
                    {{ target.database }}.information_schema.policy_references(
                        ref_entity_name => '{{ target.database }}.MARTS.DIM_PATIENT',
                        ref_entity_domain => 'TABLE'
                    )
                )
                where policy_kind = 'ROW_ACCESS_POLICY'
            {% endset %}

            {% set row_policy_result = run_query(row_policy_check_sql) %}


            {# ---------------------------------------------------------
               11. Add ROW ACCESS POLICY only if none exists
               --------------------------------------------------------- #}

            {% if row_policy_result and row_policy_result[0][0] | int == 0 %}

                {% do log(
                    "No ROW_ACCESS_POLICY found. Adding policy to DIM_PATIENT.",
                    info=True
                ) %}

                {% set row_policy_sql %}
                    alter table {{ target.database }}.MARTS.DIM_PATIENT
                    add row access policy
                        {{ target.database }}.GOVERNANCE.patient_row_access_policy
                    on (is_deceased, deceased_date)
                {% endset %}

                {% do run_query(row_policy_sql) %}

                {% do log(
                    "ROW_ACCESS_POLICY successfully added to DIM_PATIENT.",
                    info=True
                ) %}

            {% else %}

                {% do log(
                    "ROW_ACCESS_POLICY already exists on DIM_PATIENT. Skipping ADD.",
                    info=True
                ) %}

            {% endif %}

        {% else %}

            {% do log(
                "DIM_PATIENT does not exist. Skipping governance policies.",
                info=True
            ) %}

        {% endif %}

    {% endif %}
{% endmacro %}