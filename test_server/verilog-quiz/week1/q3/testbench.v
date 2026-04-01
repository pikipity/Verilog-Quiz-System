`timescale 1ns/1ps

module tb_half_adder;
    reg a, b;
    wire sum, cout;

    half_adder dut (
        .a(a),
        .b(b),
        .sum(sum),
        .cout(cout)
    );

    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_half_adder);
        
        $display("=== Test Start ===");
        
        #0 a=0; b=0;
        #1 $display("time=%0t a=%b b=%b sum=%b cout=%b", $time, a, b, sum, cout);
        
        #10 a=1; b=0;
        #1 $display("time=%0t a=%b b=%b sum=%b cout=%b", $time, a, b, sum, cout);
        
        #10 a=0; b=1;
        #1 $display("time=%0t a=%b b=%b sum=%b cout=%b", $time, a, b, sum, cout);
        
        #10 a=1; b=1;
        #1 $display("time=%0t a=%b b=%b sum=%b cout=%b", $time, a, b, sum, cout);
        
        #10 $display("=== Test End ===");
        $finish;
    end
endmodule
