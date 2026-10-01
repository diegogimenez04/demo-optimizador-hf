# model.py — extracted from starplastic.ipynb cell 1 (function_model)
# No logo, demo Grupo Investigacion
# Depends: ortools
#Librerías usadas
from datetime import datetime, timedelta
from collections import Counter

#Definimos la función modelo or-tools
###################################################################################
def function_model(lista_id,operarios,ots,maquinas,fuera_servicios,operarios_requeridos,asignacion,
                   prioridad, proc,fecha_entrega,tiinactiva,tfinactiva,changeover, fecha_inicio_plan=None):
    from datetime import datetime, timedelta
    from ortools.linear_solver import pywraplp
    # fecha_inicio_plan para agenda (fallback si no se pasa — compatible notebook)
    if fecha_inicio_plan is None:
        try:
            fecha_inicio_plan  # type: ignore
        except NameError:
            fecha_inicio_plan = globals().get('fecha_inicio_plan', datetime(2023,10,11,12,0))
    ###############################################################################
    ###############################################################################
    # Construcción modelo
    # BigM
    bigM =  2 * (sum(changeover[(j, jj)] for j, jj in changeover) + sum(proc[j] for j in proc))
    # Valor máxima prioridad
    MaximaPrioridad = max(prioridad.values())
    #SOLVER
    solver = pywraplp.Solver.CreateSolver('SCIP')

    # Parámetro primerOT
    primerOT = {}
    for m in maquinas:
        for j in ots:
            if (j, m) in asignacion.items():
                if prioridad[j] == min(prioridad[jj] for jj in ots if (jj, m) in asignacion.items()):
                    primerOT[(j, m)] = 1
                else:
                    primerOT[(j, m)] = 0


    #VARIABLES
    TF = {}
    Tard = {}
    Earl = {}
    zy = {}
    for j in ots:
        for m in maquinas:
            TF[(j, m)] = solver.NumVar(0, solver.infinity(), f'TF_{j}_{m}')
            Tard[(j, m)] = solver.NumVar(0, solver.infinity(), f'Tard_{j}_{m}')
            Earl[(j, m)] = solver.NumVar(0, solver.infinity(), f'Earl_{j}_{m}')
            for o in operarios:
                zy[(j,m,o)] = solver.IntVar(0,1,f'zy_{j}_{m}_{o}')

    #x2
    x2 = {}
    for j in ots:
        for jj in ots:
            if j != jj:
                for o in operarios:
                    x2[(j, jj, o)] = solver.IntVar(0,1,f'x2_{j}_{jj}_{o}')

    # TFo variables
    TFo = {}
    for j in ots:
        for o in operarios:
            TFo[j, o] = solver.NumVar(0, solver.infinity(), f'TFo{j},{o}')

    # Xgral(j,jj) En este modelo sería un parámetro
    xgral = {}
    #for j in ots:
    #    for jj in ots:
    #        if (j!=jj):
    #            xgral[j,jj] = solver.IntVar(0, 1, 'xgral[{},{}]'.format(j,jj))
    for m in maquinas:
        for j in ots:
            if (j, m) in asignacion.items():
                for jj in ots:
                    if jj != j and (jj,m) in asignacion.items():
                        if prioridad[j] < prioridad[jj]:
                            xgral[j,jj] = 1
                        else:
                            xgral[j,jj] = 0

    # z(j,o)
    z = {}
    for j in ots:
        for o in operarios:
            z[j,o] = solver.IntVar(0, 1, 'z[{},{}]'.format(j,o))

    # w(j,o)
    w = {}
    for j in ots:
        for o in operarios:
            w[j,o] = solver.IntVar(0, 1, 'w[{},{}]'.format(j,o))

    #Yanterior(j)
    Yanterior = {}
    for j in ots:
        Yanterior[j] = solver.IntVar(0, 1, 'Yanterior[{}]'.format(j))

    #OrdenMaquina(j,m)$asignacion(j,m)= 1+ sum(jj$asignacion(jj,m), xgral.l(j,jj))
    ordenmaquina = {}
    for j, m in asignacion.items():
        ordenmaquina[(j, m)] = 1 + sum(xgral[j, jj] for jj in ots if (jj, m) in asignacion.items()
                                           and (j!=jj))

    #x(j,jj,m) es variable fija en este modelo
    x = {}
    for m in maquinas:
        for j in ots:
            for jj in ots:
                if (j, m) in asignacion.items():
                    if (jj, m) in asignacion.items() and (j!=jj):
                        if ordenmaquina[j, m] == ordenmaquina[jj, m] + 1:
                            x[j, jj, m] = 1
                        else:
                            x[j, jj, m] = 0

    y = {}
    for j in ots:
        for m in maquinas:
            if (j,m) in primerOT:
                y[(j,m)] = primerOT[(j,m)]
            else:
                y[(j,m)] = 0

    # Makespam 1 y 2, Tardanza Total y prioOF
    Mk  = solver.NumVar(-solver.infinity(), solver.infinity(), 'Mk')
    Mk2 = solver.NumVar(-solver.infinity(), solver.infinity(), 'Mk2')
    TT  = solver.NumVar(-solver.infinity(), solver.infinity(), 'TT')
    prioOF = solver.NumVar(-solver.infinity(), solver.infinity(), 'piorFO')

    # Orden Tardía
    D = {}
    for j in ots:
        for m in maquinas:
            D[(j, m)] = solver.IntVar(0,1,f'D_{j}_{m}')

    # Otras variables
    maxT = solver.NumVar(-solver.infinity(), solver.infinity(), 'maxT')
    maxA = solver.NumVar(-solver.infinity(), solver.infinity(), 'maxA')
    NbD  = solver.NumVar(-solver.infinity(), solver.infinity(), 'NbD')
    TE   = solver.NumVar(-solver.infinity(), solver.infinity(), 'TE')


    # RESTRICCIONES (CONSTRAINTS)
    ###########################################################################

    #AsigOper(j).. sum(o,z(j,o))=e=operarios(j);
    AsigOper = {}
    for j in ots:
        # restricción de asignación de operarios
        AsigOper[j] = solver.Add(sum(z[(j,o)] for o in operarios) == operarios_requeridos[j]
                                 ,name=f'AsigOper_{j}')

    # FirstJobOP(O) .. SUM(j, W(J,O)) =e= 1;
    FirstJobOP = {}
    for o in operarios:
        FirstJobOP[o] = solver.Add(solver.Sum([w[(j, o)] for j in ots]) <= 1
                                   ,name=f'FirstJobOP_{o}')

    #FirstIntermJobOP(jj,O) ..
    #W(jj,O)+ SUM[j $(NOT SAMEAS(j,jj)), X2(j,jj,O)] =e= z(jj,o);
    FirstIntermJobOP = {}
    for jj in ots:
        for o in operarios:
            FirstIntermJobOP[(jj,o)] = solver.Add(w[(jj,o)] + sum(x2[(j,jj,o)] for j in ots if j != jj
                                                                  ) == z[(jj,o)]
                       , name=f'FirstIntermJobOP_{jj}_{o}')

    #PredecOP(jj,O) .. SUM[j $(NOT SAMEAS(j,jj)), X2(j,jj,O)] =l= z(jj,o) ;
    PredecOP = {}
    for o in operarios:
        for jj in ots:
            PredecOP[(jj,o)]=solver.Add(sum(x2[j,jj,o] for j in ots if j != jj) <= z[(jj,o)]
                                        , name=f'PredecOP_{jj}_{o}')


    #SucesOP(j,O) .. SUM[jj $(NOT SAMEAS(j,jj)), X2(j,jj,O)] =l= z(j,o) ;
    SucesOP = {}
    for o in operarios:
        for j in ots:
            SucesOP[(j,o)] = solver.Add(sum(x2[(j,jj,o)] for jj in ots if j!=jj) <= z[(j,o)],
                       name=f'SucesOP_{j}_{o}')


    #tiempoFinOP(j,jj,O)$(NOT SAMEAS(j,jj)).. TFo(jj,O) =g= TFo(j,O)+proc(jj)
    #                                 + changeover(j,jj)-(1-X2(j,jj,O))*bigM ;
    tiempoFinOP = {}
    for jj in ots:
        for j in ots:
            if j != jj:
                for o in operarios:
                    tiempoFinOP[(j,jj,o)] = solver.Add(TFo[jj, o] >= TFo[j, o] + proc[jj] + changeover[j, jj
                    ] - (1 - x2[j, jj, o]) * bigM, name=f'tiempoFinOP_{j}_{jj}_{o}')

    # tiempoFinFirstJobOP(j,O).. TFo(j,O) =g= proc(j)*w(j,O);
    tiempoFinFirstJobOP = {}
    for j in ots:
        for o in operarios:
            tiempoFinFirstJobOP[(j,o)] = solver.Add(TFo[j, o] >= proc[j] * w[(j, o)], name=f'tiempoFinFirstJobOP_{j}_{o}')

    #tfoUB(j,o).. TFo(j,o) =l= BigM * z(j,o);
    TFoUB = {}
    for j in ots:
        for o in operarios:
            TFoUB[(j,o)]  =solver.Add(TFo[j, o] <= bigM * z[j, o]
                                      ,name=f'TFoUB_{j}_{o}')

    #AsigFirst(j,o)..  W(J,O)=l= z(j,o);
    AsigFirst = {}
    for j in ots:
        for o in operarios:
            AsigFirst[(j,o)] = solver.Add(w[(j,o)] <= z[(j, o)],
                                          name=f'AsigFirst_{j}_{o}')


    #Log1(j,m,o)$Asignacion(j,m).. zy(j,m,o) =e= z(j,o) ;
    Log1 = {}
    for j,m in asignacion.items():
        for o in operarios:
            # restricción de equivalencia de variables
            Log1[(j,m,o)] = solver.Add(zy[(j,m,o)] == z[(j,o)], name=f'Log1_{j}_{m}_{o}' )

    # Log4(j,m,o)$(not Asignacion(j,m)).. zy(j,m,o) =e= 0  ;
    Log4 = {}
    for j in ots:
        for m in maquinas:
            if (j, m) not in asignacion.items():
                Log4[(j,m,o)] = solver.Add(zy[j, m, o] == 0, name=f'Log4_{j}_{m}_{o}'
                                           )
    # Log5(j,m)$Asignacion(j,m).. sum(o,zy(j,m,o)) =e= operarios(j);
    Log5 = {}
    for j,m in asignacion.items():
            Log5[(j,m)] = solver.Add(sum(zy[(j, m, o)] for o in operarios) == operarios_requeridos[j]
                       , name=f'Log5_{j}_{m}')

    # IgualTF1(j,m,o)$Asignacion(j,m).. tf(j,m) =g= tfo(j,o) - bigm * (1- zy(j,m,o));
    IgualTF1 ={}
    for j, m in asignacion.items():
        for o in operarios:
            IgualTF1[(j,m,o)] = solver.Add(TF[(j, m)] >= TFo[(j,o)] - bigM * (1-zy[(j, m, o)])
                       ,name='IgualTF1_{j}_{m}_{o}')

    # IgualTF2(j,m,o)$Asignacion(j,m).. tf(j,m) =l= tfo(j,o) + bigm * (1- zy(j,m,o));
    IgualTF2 = {}
    for j, m in asignacion.items():
        for o in operarios:
            IgualTF2[(j,m,o)] = solver.Add(TF[(j, m)] <= TFo[(j,o)] + bigM * (1-zy[(j, m, o)])
                         ,name='IgualTF2_{j}_{m}_{o}')

    # FirstJob(m) .. SUM(j$Asignacion(j,m), Y(j,m)) =e= 1;
    FirstJob = {}
    for m in maquinas:
        FirstJob[(m)] = solver.Add(sum(y[(j, m)] for j in ots if (j, m) in asignacion.items()) == 1)


    # FirstIntermJob(jj,m)$Asignacion(jj,m) ..
    # Y(jj,m)+ SUM[j $(Asignacion(j,m) and(NOT SAMEAS(j,jj))), X(j,jj,m)] =e= 1;
    FirstIntermJob = {}
    for (jj, m) in asignacion.items():
        FirstIntermJob[(jj,m)] = solver.Add(y[(jj,m)] + sum(x[(j,jj,m)] for (j,m) in
                                                        filter(lambda jm: jm[1]==m and jm[0]!=jj
                                                              , asignacion.items())) == 1)

    #Predec(jj,m)$Asignacion(jj,m) ..
    # SUM[j $(Asignacion(j,m) and (NOT SAMEAS(j,jj))),X(j,jj,m)] =l= 1 ;
    Predec = {}
    for jj, m in asignacion.items():
        Predec[(jj,m)] = solver.Add(sum(x[(j,jj,m)
                        ] for (j,m) in filter(lambda jm: jm[1]==m and jm[0]!=jj
                                              ,asignacion.items())) <= 1)

    #Suces(j,m)$Asignacion(j,m) ..
    # SUM[jj $(Asignacion(jj,m) and(NOT SAMEAS(j,jj))), X(j,jj,m)] =l= 1 ;
    Suces = {}
    for j, m in asignacion.items():
        Suces[(j,m)] = solver.Add(sum(x[(j,jj,m)
                        ] for (jj,m) in filter(lambda jm: jm[1]==m and jm[0]!=j
                                               ,asignacion.items())) <= 1)

    #tiempoFin(j,jj,m)$(Asignacion(j,m) and Asignacion(jj,m) and (NOT SAMEAS(j,jj)))
    #.. TF(jj,m) =g= TF(j,m)+proc(jj)+ changeover(j,jj)-(1-X(j,jj,m))*bigM ;
    tiempoFin = {}
    for jj, mm in asignacion.items():
        for j, m in asignacion.items():
            if mm==m and j != jj:
                tiempoFin[(j,jj,m)] = solver.Add(TF[(jj, m)] >= TF[(j, m)] + proc[jj] + changeover[(j, jj)
                            ] - (1 - x[(j, jj, m)]) * bigM)

    #tiempoFinFirstJob(j,m)$Asignacion(j,m) .. TF(j,m) =g= proc(j)*Y(j,m);
    tiempoFinFirstJob = {}
    for j, m in asignacion.items():
        tiempoFinFirstJob[(j,m)] = solver.Add(TF[(j,m)] >= proc[j] * y[(j,m)])

    #tiempofinfirstjob2(j,m)$(asignacion(j,m) and (Prioridad(j) eq 1)).. tf(j,m) =e= proc(j);
    tiempofinfirstjob2 = {}
    for j, m in asignacion.items():
        if prioridad[j] == 1:
            tiempofinfirstjob2[(j,m)] = solver.Add(TF[(j, m)] == proc[j])

    #maqFS1(j,m)$(asignacion(j,m) and fueraservicio(m))..
    # tf(j,m)=l=tiinactiva(m)+BigM*(1-Yanterior(j));
    maqFS1 = {}
    for j, m in asignacion.items():
        if m in fuera_servicios:
            maqFS1[(j,m)] = solver.Add(TF[j, m] <= tiinactiva[m] + bigM * (1 - Yanterior[j]))

    #maqFS2(j,m)$(asignacion(j,m) and fueraservicio(m))..
    #tf(j,m)-proc(j)=g= tfinactiva(m)*(1-Yanterior(j));
    maqFS2 = {}
    for j, m in asignacion.items():
        if m in fuera_servicios:
            maqFS2[(j,m)] = solver.Add(TF[j, m] - proc[j] >= tfinactiva[m] * (1 - Yanterior[j]))

    #precedenciaGral(j,jj,m)$((Asignacion(j,m))
    # and (Asignacion(jj,m))
    # and (ord(j) ne ord(jj)))..
    #                 TF(jj,m) =g= TF(j,m)-(1-Xgral(j,jj))*bigM  ;
    precedenciaGral = {}
    for j, m in asignacion.items():
        for jj, mm in asignacion.items():
            if j != jj and m == mm:
                precedenciaGral[(j,jj,m)] = solver.Add(TF[(jj, m)] >= TF[(j, m)
                                            ] - (1 - xgral[(j, jj)]) * bigM)

    # noasignar(j,m)$(not Asignacion(j,m))..  Y(j,m)=e=0;
    noasignar = {}
    for j in ots:
        for m in maquinas:
            if (j, m) not in asignacion.items():
                noasignar[(j,m)] = solver.Add(y[(j, m)] == 0)

    # makespanDef(j,m)$Asignacion(j,m) .. Mk =g= TF(j,m) ;
    makespanDef = {}
    for j, m in asignacion.items():
        makespanDef[(j,m)] = solver.Add(Mk >= TF[(j, m)], name='makespanDef_{j}_{m}')

    # makespanDef2(j,o) .. Mk2 =g= TFo(j,o) ;
    makespanDef2 = {}
    for j in ots:
        for o in operarios:
            makespanDef2[(j,o)] = solver.Add(Mk2 >= TFo[(j, o)], name='makespanDef2_{j}_{o}')

    #minPrioridad(j,m)$(Asignacion(j,m))..
    #(tf(j,m))*(maximaprioridad+1-prioridad(j)+Mk)=l= prioOF;
    minPrioridad = {}
    for j,m in asignacion.items():
        minPrioridad[(j,m)] = solver.Add(TF[(j,m)]*(MaximaPrioridad + 1 - prioridad[j]
                                                    ) + Mk <= prioOF)

    #Check Constraint Total
    print('Number of partial constraints =', solver.NumConstraints())

    #Parámetros del Solver
    solver.Minimize(prioOF)
    solver.set_time_limit(30000)
    gap = 0.0
    solverParams = pywraplp.MPSolverParameters()
    solverParams.SetDoubleParam(solverParams.RELATIVE_MIP_GAP, gap)
    status = solver.Solve(solverParams)


    if status == pywraplp.Solver.OPTIMAL:
        print("Solución óptima")
        print('Objective value =', solver.Objective().Value())
        print(prioOF.name(),'=', prioOF.solution_value())
        print('relative gap (%):', (solver.Objective().Value()-solver.Objective(
              ).BestBound())/solver.Objective().BestBound()*100)
        print()
        print('Problem solved in %f milliseconds' % solver.wall_time())
        print('Problem solved in %d iterations' % solver.iterations())
        print('Problem solved in %d branch-and-bound nodes' % solver.nodes())

    elif status == pywraplp.Solver.FEASIBLE:
        print("Solución factible")
        print('Objective value =', solver.Objective().Value())
        print(prioOF.name(),'=', prioOF.solution_value())
        print('relative gap (%):', (solver.Objective().Value
                                    ()-solver.Objective(
              ).BestBound())/solver.Objective().BestBound()*100)
        print()
        print('Problem solved in %f milliseconds' % solver.wall_time())
        print('Problem solved in %d iterations' % solver.iterations())
        print('Problem solved in %d branch-and-bound nodes' % solver.nodes())
    elif status == pywraplp.Solver.INFEASIBLE:
        print('El problema es infactible')
        print('Objective value =', solver.Objective().Value())
        print(prioOF.name(),'=', prioOF.solution_value())
        # esto se deshabilita porque da division por 0 si es INFEASIBLE
        # print('relative gap (%):', (solver.Objective().Value()-solver.Objective(
        #       ).BestBound())/solver.Objective().BestBound()*100)
        # print()
        # print('Problem solved in %f milliseconds' % solver.wall_time())
        # print('Problem solved in %d iterations' % solver.iterations())
        # print('Problem solved in %d branch-and-bound nodes' % solver.nodes())
        # SI DA INFEASIBLE, TIENE QUE SALIR
        print('===> PROBLEMA INFACTIBLE')
        return {}

    ###############################################################################
    ###############################################################################
    # model output

    model_output = {}

    # IndicadoresPerformance('CompletamientoOrdenes')= Mk.l;
    tiempo_fin = {}
    max_TF = 0
    for j,m in asignacion.items():
            if (TF[j,m].solution_value() > 0):
                tiempo_fin[j,m] = TF[j,m].solution_value()
                max_TF = max(max_TF,tiempo_fin[j,m])
    model_output['completamiento_ordenes'] = max_TF

    #IndicadoresPerformance('TardanzaTotal')= tt.l;
    model_output['tardanza_total'] = TT.solution_value()

    #IndicadoresPerformance('AnticipacionTotal')= te.l  ;
    model_output['anticipacion_total'] = TE.solution_value()

    #IndicadoresPerformance('MaximaTardanza')= maxT.l ;
    maxT_result = 0
    for j in ots:
        for m in maquinas:
            maxT_result = max(maxT_result,Tard[(j,m)].solution_value())
    model_output['maxima_tardanza'] = maxT_result

    #IndicadoresPerformance('MaximaAnticipacion')=maxA.l;
    maxA_result = 0
    for j in ots:
        for m in maquinas:
            maxA_result = max(maxA_result,Earl[(j,m)].solution_value())
    model_output['maxima_anticipacion'] = maxA_result

    #IndicadoresPerformance('TotalSetup')=sum((j,jj,m), changeover(j,jj)*x.l(j,jj,m));
    TotalSetup = 0
    for m in maquinas:
        for j in ots:
            for jj in ots:
                if (j, m) in asignacion.items():
                    if (jj, m) in asignacion.items() and (j!=jj):
                        TotalSetup = TotalSetup + changeover[(j, jj)] * x[(j, jj, m)]
    model_output['total_setup'] = TotalSetup

    #IndicadoresPerformance('TotalProduccion')=sum((j), proc(j));
    model_output['total_produccion'] = sum(proc[j] for j in ots)

    #EstadoOrdenes('OrdenesTardias')= nbd.l/card(j);
    model_output['ordenes_tardias'] = NbD.solution_value()/len(ots)

    #EstadoOrdenes('OrdenesAnticipadas')=(card(j)-nbd.l)/card(j);
    model_output['ordenes_anticipadas'] = (len(ots)-NbD.solution_value())/len(ots)

    #uso_operarios_total (tiempo_prod_total= sum((j,o), tiempo_productivo(j,o));)
    tiempo_productivo = {}
    for j in ots:
        for o in operarios:
            zl = z[j,o].solution_value()
            tiempo_productivo[j,o] = proc[j]*zl + sum(changeover[j,jj
                                        ]*x2[(j, jj, o)
                                         ].solution_value() for jj in ots if jj!=j)

    tiempo_prod_total = sum(tiempo_productivo[j, o] for (j, o) in tiempo_productivo)
    model_output['uso_operarios_total'] = tiempo_prod_total

    #productividad_operarios (Productividad = tiempo_prod_total/(card(o)* mk.l);)
    Productividad = tiempo_prod_total/(len(operarios)* max_TF) ;
    model_output['productividad_operarios'] = Productividad

    formato = '%d/%m/%Y %H:%M'
    agenda_maquina_ot = []
    agenda_personal = []
    for i in lista_id:
            #if (TF[j,m].solution_value() > 0):
            fecha_inicio = fecha_inicio_plan + timedelta(hours=TF[i['ot'],i['maquina']
                                            ].solution_value() - proc[i['ot']])
            fecha_fin = fecha_inicio_plan + timedelta(hours=TF[i['ot'],i['maquina']].solution_value())
            agenda_maquina_ot.append({
                    'id': i['id'],
                    'ot_nro': i['ot'],
                    'maquina_nro': i['maquina'],
                    'hora_inicio': fecha_inicio.strftime(formato),
                    'hora_fin': fecha_fin.strftime(formato)
                    })
            agenda_personal.append({
                    'id': i['id'],
                    'cant_personal': operarios_requeridos[i['ot']],
                    'hora_inicio': fecha_inicio.strftime(formato),
                    'hora_fin': fecha_fin.strftime(formato)})

    model_output['agenda_maquina_ot'] = agenda_maquina_ot
    model_output['agenda_personal'] = agenda_personal

    return model_output
###############################################################################
###########################TERMINA FUNCTION_MODEL##############################