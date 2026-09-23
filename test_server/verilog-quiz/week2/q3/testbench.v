`timescale 1ns/1ps

module tb_half_adder;
    reg a;
    reg b;
    reg sum;
    wire cout;

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
        
        // Test case 1
        #0 a=0; b=0; sum=0;
        #1 $display("time=%0t a=%b b=%b sum=%b cout=%b", $time, a, b, sum, cout);

        // Test case 2
        #10 a=0; b=1; sum=0;
        #1 $display("time=%0t a=%b b=%b sum=%b cout=%b", $time, a, b, sum, cout);

        #10 $display("=== Test End ===");
        $finish;
    end
endmodule
