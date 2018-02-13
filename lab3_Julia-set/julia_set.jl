using Plots
Plots.gr()

function set_workers(target)
    if nprocs() == 1
        addprocs(1)
    end
        
    current = nworkers()
    if current < target
        addprocs(target - current)
    elseif current > target
        rmprocs(workers()[end - (current - target - 1):end])
    end
end

# set_workers(4)

# punkt o współrzędnych (x,y) należy do zbioru Julii o parametrze c 
# jeśli dla liczby zespolonej z=x+i*y
# ciąg zₙ₊₁=zₙ²+c , nie dąży do nieskończoności

# dążenie do nieskończoności sprawdzamy ustawiająć maksymalną liczbę iteracji i sprawdzając
# czy kolejne wyrazy ciągu nie przekroczą zadanego progu (tutaj 2) w tej (bądź mniejszej)
# liczbie iteracji

# funkcja sprawdzająca, czy punkt z należy do zbioru Julii o parametrze c
@everywhere function generate_julia(z; c=2, maxiter=200)
    for i=1:maxiter
        if abs(z) > 2
            return i-1
        end
        z = z^2 + c
    end
    return maxiter
end

# wypełnianie tablicy liczbami złożonymi
@everywhere function initialize_array(array, height, width, xrange, yrange)
    for x in 1:width
        for y in 1:height
            array[x, y] = xrange[x] + 1im * yrange[y]
        end
    end
    return array
end

# główna funkcja 
@everywhere function main(height, width, julia_calculator, array_factory, make_plot=true)
    # ustawiamy płaszczyznę
    xmin, xmax = -2,2
    ymin, ymax = -1,1
    xrange = linspace(xmin, xmax, width)
    yrange = linspace(ymin, ymax, height)
    
    # obliczamy
    julia_set = array_factory(width, height)
    initialize_array(julia_set, height, width, xrange, yrange)
    julia_set = julia_calculator(julia_set, height, width)
    
    # rysujemy
    if make_plot
        return Plots.heatmap(xrange, yrange, convert(Array{Int64}, julia_set))
    end
end

@everywhere function standard_array(width, height)
    return Array{Complex{Float64}}(width, height)
end

@everywhere function shared_array(width, height)
    return SharedArray{Complex{Float64}}(width, height)
end

@everywhere function sequential_calculator(array, height, width, maxiter=200)
   for x in 1:height
        for y in 1:width
            array[x, y] = generate_julia(array[x, y], c=-0.70176-0.3842im, maxiter=maxiter)
        end
    end
    return array
end

@everywhere function parallel_calculator(array, height, width, maxiter=200)    
    @sync @parallel for x in 1:height
        for y in 1:width
            array[x, y] = generate_julia(array[x, y], c=-0.70176-0.3842im, maxiter=maxiter)
        end
    end
    return array
end

@everywhere function pmap_calculator(array, height, width, maxiter=200)
    pmap_fun(z) = convert(Complex{Float64}, generate_julia(z, c=-0.70176-0.3842im, maxiter=maxiter))
    return pmap(pmap_fun, array)
end

function batch()
    repeats = 4

    println("name", "\t", "workers", "\t", "size", "\t", "repeapt", "\t", "time")

    for workers in 4:-1:1
        set_workers(workers)
        for param in [("parallel", parallel_calculator, shared_array), ("pmap", pmap_calculator, shared_array)]
            (name, julia_calculator, array_factory) = param
            for n in [1000, 4000]
                for i in 1:repeats
                    elapsed = @elapsed(main(n, n, julia_calculator, array_factory, false))
                    println(name, "\t", nworkers(), "\t", n, "\t", i, "\t", elapsed)
                end
            end
        end
    end

    for n in [1000, 4000]
        for i in 1:repeats
            elapsed = @elapsed(main(n, n, sequential_calculator, standard_array, false))
            println("seq", "\t", nworkers(), "\t", n, "\t", i, "\t", elapsed)
        end
    end
end

function task(name, problem_size)
    if name == "seq"
        julia_calculator = sequential_calculator
        array_factory = standard_array
    elseif name == "parallel"
        julia_calculator = parallel_calculator
        array_factory = shared_array
    elseif name == "pmap"
        julia_calculator = pmap_calculator
        array_factory = shared_array
    end
    
    main(problem_size, problem_size, julia_calculator, array_factory, false)
end


worker_procs = parse(Int, ARGS[1])
name = ARGS[2]
problem_size = parse(Int, ARGS[3])

# Dummy
task(name, 10)

elapsed = @elapsed(task(name, problem_size))
println(name, "\t", nworkers(), "\t", problem_size, "\t", elapsed)
